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


struct Visitor {}

impl Visitor {
    fn new() -> Self { Self {} }

    fn visit(&self, py: Python, obj: ast::Document<String>) -> Document {
        Document {
            definitions: obj.definitions
                .iter()
                .map(|definition| self.visit_definition(py, definition))
                .collect::<Vec<_>>()
                .to_object(py)
        }
    }

    fn visit_definition(&self, py: Python, definition: &ast::Definition<String>) -> PyObject {
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

    fn visit_selection(&self, py: Python, selection: &ast::Selection<String>) -> PyObject {
        match selection {
            ast::Selection::Field(field) => {
                Field {
                    alias: field.alias.clone(),
                    name: field.name.to_string(),
                }.into_py(py)
            },
            _ => unreachable!()
        }
    }
}

#[pyfunction]
fn parse(query: String) -> PyResult<Document> {
    let ast_ = parse_query::<String>(&query).unwrap();
    Python::with_gil(|py| {
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
