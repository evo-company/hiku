use std::marker::PhantomData;

use pyo3::prelude::*;
use pyo3::types::PyList;
use graphql_parser::parse_query;
use graphql_parser::query as ast;


#[pyclass]
#[derive(Debug, Clone)]
struct DocumentNode {
    #[pyo3(get)]
    kind: String,
    #[pyo3(get)]
    definitions: PyObject,
}


#[pyclass]
#[derive(Debug, Clone)]
struct SelectionSetNode {
    #[pyo3(get)]
    kind: String,
    #[pyo3(get)]
    selections: PyObject,
}


#[pyclass]
#[derive(Debug, Clone)]
struct OperationDefinitionNode {
    #[pyo3(get)]
    kind: String,
    #[pyo3(get)]
    operation: String,
    #[pyo3(get)]
    name: Option<String>, // TODO must be a NameNode
    #[pyo3(get)]
    selection_set: PyObject,
    #[pyo3(get)]
    variable_definitions: PyObject,
}

#[pyclass]
#[derive(Debug, Clone)]
struct NameNode {
    #[pyo3(get)]
    kind: String,
    #[pyo3(get)]
    value: String,
}

#[pyclass]
#[derive(Debug, Clone)]
struct FieldNode {
    #[pyo3(get)]
    kind: String,
    #[pyo3(get)]
    alias: Option<String>,
    #[pyo3(get)]
    name: PyObject,
    #[pyo3(get)]
    directives: PyObject,
    #[pyo3(get)]
    arguments: PyObject,
    #[pyo3(get)]
    selection_set: PyObject,
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

    fn visit(&self, py: Python, obj: ast::Document<'a, &'a str>) -> DocumentNode {
        DocumentNode {
            kind: "document".to_string(),
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
                        let selections = set.items.iter().map(|selection| {
                            self.visit_selection(py, selection)
                        }).collect::<Vec<_>>().to_object(py);

                        let selection_set = SelectionSetNode {
                            kind: "selection_set".to_string(),
                            selections
                        }.into_py(py);
                        OperationDefinitionNode {
                            kind: "operation_definition".to_string(),
                            operation: "query".to_string(),
                            name: None,
                            selection_set,
                            variable_definitions: PyList::empty(py).to_object(py),
                        }.into_py(py)
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
                FieldNode {
                    kind: "field".to_string(),
                    alias: field.alias.map(|alias| alias.to_string()),
                    name: NameNode {
                        kind: "name".to_string(),
                        value: field.name.to_string()
                    }.into_py(py),
                    directives: PyList::empty(py).to_object(py),
                    arguments: PyList::empty(py).to_object(py),
                    selection_set: py.None(),
                }.into_py(py)
            },
            _ => unreachable!()
        }
    }
}

#[pyfunction]
fn parse(query: String) -> PyResult<DocumentNode> {
    Python::with_gil(|py| {
        let ast_ = parse_query::<&str>(&query).unwrap();
        let doc = Visitor::new().visit(py, ast_);
        Ok(doc)
    })
}

fn add_ast_module(_py: Python, parent: &PyModule) -> PyResult<()> {
    let m = PyModule::new(_py, "ast")?;
    m.add_class::<DocumentNode>()?;
    m.add_class::<OperationDefinitionNode>()?;
    m.add_class::<SelectionSetNode>()?;
    m.add_class::<NameNode>()?;
    m.add_class::<FieldNode>()?;
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
