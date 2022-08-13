use pyo3::prelude::*;
use graphql_parser::parse_query;
use apollo_parser::Parser;
use apollo_parser::ast;

// TODO: How to translate rust ast to python ?
// 1. Use graphql-core
// 2. write all ast in pyo3


#[pyclass(subclass)]
struct Node {
   #[pyo3(get)]
   kind: String
}

#[pymethods]
impl Node {
    #[new]
    /// TODO: how to implement ref string more cool ?
    fn new(kind: &str) -> Self {
        Node { kind: kind.into() }
    }
}

#[pyclass(extends=Node)]
struct DocumentNode {
    // #[pyo3(get)]
    // pub definitions: Vec<DefinitionNode>,
}

#[pymethods]
impl DocumentNode {
    #[new]
    fn new() -> (Self, Node) {
        // let definitions = vec![];
        // (DocumentNode { definitions }, Node::new("document"))
        (DocumentNode { }, Node::new("document"))
    }
}

// #[pyclass(extends=Node, subclass)]
// struct ValueNode { }
//
// #[pymethods]
// impl ValueNode {
//     #[new]
//     fn new() -> (Self, Node) {
//         (ValueNode { }, Node::new("value"))
//     }
// }
//
// #[pyclass(extends=Node, subclass)]
// struct TypeNode { }
//
// #[pymethods]
// impl TypeNode {
//     #[new]
//     fn new() -> (Self, Node) {
//         (TypeNode { }, Node::new("type"))
//     }
// }
//
// #[derive(Clone)]
// #[pyclass(extends=Node)]
// struct NameNode {
//     value: String
// }
//
// #[pymethods]
// impl NameNode {
//     #[new]
//     fn new(value: String) -> (Self, Node) {
//         (NameNode { value }, Node::new("name"))
//     }
// }

// -------------ADVANCED-------------------

// #[derive(Clone)]
// #[pyclass(extends=ValueNode)]
// struct VariableNode {
//     name: NameNode
// }
//
// #[pymethods]
// impl VariableNode {
//     #[new]
//     fn new(name: String) -> PyClassInitializer<Self> {
//         let (name_node) = NameNode::new(name);
//         PyClassInitializer::from(ValueNode::new())
//             .add_subclass(VariableNode {
//                 name: name_node
//             })
//     }
// }
//
// #[pyclass(extends=Node)]
// struct VariableDefinitionNode {
//     variable: VariableNode,
//     #[pyo3(get, name = "type")]
//     type_: TypeNode,
//     default_value: Option<ValueNode>,
//     // directives
// }
//
// #[pyclass]
// struct Variable {
//     name: NameNode
// }
//
// #[pyclass(extends=Node, subclass)]
// struct DefinitionNode {
//
// }
//
// #[pyclass(extends=Node, subclass)]
// struct SelectionNode {
//     // directives: Vec
// }
//
// #[pyclass(extends=Node)]
// struct SelectionSetNode {
//     selections: Vec<SelectionNode>
// }
//
// #[pyclass(extends=DefinitionNode, subclass)]
// struct ExecutableDefinitionNode {
//     name: Option<NameNode>,
//     // directives
//     variable_definitions: Vec<VariableDefinitionNode>,
//     selection_set: SelectionSetNode
// }
//
// #[pymethods]
// impl ExecutableDefinitionNode {
//     #[new]
//     fn new() -> PyClassInitializer<Self> {
//         PyClassInitializer::from(DefinitionNode::new())
//             .add_subclass(ExecutableDefinitionNode {
//                 name: Some(NameNode::new("XUser")),
//                 variable_definitions: vec![],
//                 selection_set: SelectionSetNode::new(vec![])
//             })
//     }
// }
//
// #[pyclass]
// enum OperationType {
//     Query,
// }
//
// #[pyclass(extends=ExecutableDefinitionNode)]
// struct OperationDefinitionNode {
//     operation: Option<OperationType>,
// }
//
// #[pymethods]
// impl OperationDefinitionNode {
//     #[new]
//     fn new () -> PyClassInitializer<Self> {
//         PyClassInitializer::from(ExecutableDefinitionNode::new())
//             .add_subclass(OperationDefinitionNode {
//                 operation: Some(OperationType::Query)
//             })
//     }
//    fn from_ast(od: ast::OperationDefinition) -> Self {
//        OperationDefinitionNode {
//            operation: Some(OperationType::Query),
//            name: Some(NameNode { value: String::from("XUser") }),
//            variable_definitions: vec![],
//            selection_set: Some(SelectionSet {
//                selections: vec![
//                    SelectionNode {
//                        kind: String::from("field")
//                    }
//                ]
//            })
//        }
//    }
// }
//
// impl From<ast::OperationDefinition> for OperationDefinitionNode {
//     fn from(od: ast::OperationDefinition) -> Self {
//         OperationDefinitionNode::from_ast(od)
//     }
// }

#[pyfunction]
fn parse_apollo(query: String) -> PyResult<Node> {
    let parser = Parser::new(&query);
    let parsed_ast = parser.parse();
    // let (doc, base) = DocumentNode::new();
    let doc = Node { kind: String::from("node") };
    Ok(doc)
}

#[pyfunction]
fn parse_graphql_parser(query: String) -> PyResult<Node> {
    let ast_ = parse_query::<&str>(&query).unwrap();
    // let (doc, base) = DocumentNode::new();
    let doc = Node { kind: String::from("node") };
    Ok(doc)
}

/// A Python module implemented in Rust.
/// TODO: maybe rename module
#[pymodule]
fn hiku_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_apollo, m)?)?;
    m.add_function(wrap_pyfunction!(parse_graphql_parser, m)?)?;
    m.add_class::<DocumentNode>()?;
    m.add_class::<Node>()?;
    // m.add_class::<ValueNode>()?;
    // m.add_class::<NameNode>()?;
    // m.add_class::<TypeNode>()?;

    // m.add_class::<DefinitionNode>()?;
    // m.add_class::<OperationDefinition>()?;
    // m.add_class::<SelectionSet>()?;
    // m.add_class::<SelectionNode>()?;
    Ok(())
}
