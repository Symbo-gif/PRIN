//! Fixture crate root for the Rust adapter tests.

pub mod foo;

use serde::Serialize;

pub struct Widget {
    pub name: String,
}

pub fn make_widget() -> Widget {
    Widget { name: "widget".to_string() }
}

#[test]
fn test_make_widget() {
    assert_eq!(make_widget().name, "widget");
}
