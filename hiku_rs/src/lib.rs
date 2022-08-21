use std::marker::PhantomData;
use pyo3::prelude::*;
use graphql_parser::parse_query;
use graphql_parser::query as ast;


#[pyclass]
#[derive(Debug, Clone)]
struct Document {
    #[pyo3(get)]
    definitions: PyObject,
}


#[pyclass]
#[derive(Debug, Clone)]
struct SelectionSet {
    #[pyo3(get)]
    items: PyObject,
}


#[pyclass]
#[derive(Debug, Clone)]
struct Field {
    #[pyo3(get)]
    alias: Option<String>,
    #[pyo3(get)]
    name: String,
    // pub arguments: Vec<(T::Value, Value)>,
    // pub directives: Vec<Directive>,
    // #[pyo3(get)]
    // pub selection_set: SelectionSet,
}


struct Visitor<'a, T> {
    phantom: PhantomData<&'a T>
}

impl<'a> Visitor<'a, &str> {
    fn new() -> Self {
        Self {
            phantom: PhantomData
        }
    }

    fn visit(&self, py: Python, obj: ast::Document<'a, &'a str>) -> Document {
        Document {
            definitions: obj.definitions
                .iter()
                .map(|definition| self.visit_definition(py, definition))
                .collect::<Vec<_>>()
                .to_object(py)
        }
    }

    fn visit_definition(&self, py: Python, definition: &ast::Definition<'a, &'a str>) -> PyObject {
        match definition {
            ast::Definition::Operation(op) => {
                match op {
                    ast::OperationDefinition::SelectionSet(set) => {
                        let items = set.items.iter().map(|selection| {
                            self.visit_selection(py, selection)
                        }).collect::<Vec<_>>().to_object(py);
                        SelectionSet { items }.into_py(py)
                    },
                    _ => unreachable!()
                }
            },
            _ => unreachable!()
        }
    }

    fn visit_selection(&self, py: Python, selection: &ast::Selection<'a, &'a str>) -> PyObject {
        match selection {
            ast::Selection::Field(field) => {
                Field {
                    alias: field.alias.map(|alias| alias.to_string()),
                    name: field.name.to_string(),
                }.into_py(py)
            },
            _ => unreachable!()
        }
    }
}

#[pyfunction]
fn parse(query: String) -> PyResult<Document> {
    Python::with_gil(|py| {
        let ast_ = parse_query::<&str>(&query).unwrap();
        let doc = Visitor::new().visit(py, ast_);
        Ok(doc)
    })
}

fn add_ast_module(_py: Python, parent: &PyModule) -> PyResult<()> {
    let m = PyModule::new(_py, "ast")?;
    m.add_class::<Document>()?;
    m.add_class::<SelectionSet>()?;
    m.add_class::<Field>()?;
    parent.add_submodule(m)
}

fn add_parser_module(_py: Python, parent: &PyModule) -> PyResult<()> {
    let m = PyModule::new(_py, "parser")?;
    m.add_function(wrap_pyfunction!(parse, m)?)?;
    parent.add_submodule(m)
}

#[pymodule]
fn hiku_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    add_parser_module(_py, m)?;
    add_ast_module(_py, m)?;
    Ok(())
}


#[cfg(test)]
mod tests {
    use pyo3::AsPyPointer;
    use crate::parse;

    #[test]
    fn test_simple_query() {
        pyo3::prepare_freethreaded_python();
        let ast = parse("{ name }".to_string()).unwrap();
        assert!(!ast.definitions.as_ptr().is_null())
    }
}
