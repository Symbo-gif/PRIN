//! Fixture submodule for the Rust `mod` resolution test.

pub trait Greeter {
    fn greet(&self) -> String;
}

pub enum Mood {
    Happy,
    Sad,
}
