//! Minimal, allocation-bounded ONNX (protobuf) graph inspection.
//!
//! The subconscious controller must be able to state *what* it is about to
//! execute before it hands a file to an external inference runtime: the graph
//! name, IR/opset versions, and the exact name, element type, and shape of
//! every graph input and output. This module reads those fields — and only
//! those fields — directly from the serialized `ModelProto`, so validation is
//! independent of whether ONNX Runtime is installed and of which execution
//! provider would be selected.
//!
//! Only the following `onnx.proto` fields are decoded; every other field is
//! skipped by wire type without being interpreted:
//!
//! | Message | Fields |
//! |---|---|
//! | `ModelProto` | 1 `ir_version`, 2 `producer_name`, 3 `producer_version`, 7 `graph`, 8 `opset_import` |
//! | `OperatorSetIdProto` | 1 `domain`, 2 `version` |
//! | `GraphProto` | 1 `node`, 2 `name`, 5 `initializer`, 11 `input`, 12 `output` |
//! | `NodeProto` | 4 `op_type` |
//! | `TensorProto` | 1 `dims`, 2 `data_type`, 8 `name`, 13 `external_data`, 14 `data_location` |
//! | `StringStringEntryProto` | 1 `key`, 2 `value` |
//! | `ValueInfoProto` | 1 `name`, 2 `type` |
//! | `TypeProto` | 1 `tensor_type` |
//! | `TypeProto.Tensor` | 1 `elem_type`, 2 `shape` |
//! | `TensorShapeProto` | 1 `dim` |
//! | `TensorShapeProto.Dimension` | 1 `dim_value`, 2 `dim_param` |
//!
//! The reader is total: every malformed input produces
//! [`DaemonError::MalformedOnnx`] rather than a panic, and nesting depth is
//! fixed by this module (unknown nested messages are skipped, never recursed
//! into), so untrusted input cannot drive unbounded recursion.

use std::fmt;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::DaemonError;

/// `TensorProto.DataType.FLOAT` — the only element type the controller
/// contract accepts.
pub const ELEM_TYPE_FLOAT: i32 = 1;

/// `TensorProto.DataLocation.EXTERNAL`.
const DATA_LOCATION_EXTERNAL: i64 = 1;

/// Protobuf wire type: base-128 varint.
const WIRE_VARINT: u8 = 0;
/// Protobuf wire type: fixed 64-bit.
const WIRE_I64: u8 = 1;
/// Protobuf wire type: length-delimited.
const WIRE_LEN: u8 = 2;
/// Protobuf wire type: fixed 32-bit.
const WIRE_I32: u8 = 5;

/// One dimension of an ONNX tensor shape.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Dim {
    /// A statically known extent (`dim_value`).
    Fixed(i64),
    /// A symbolic extent such as `"batch"` (`dim_param`).
    Param(String),
    /// Neither `dim_value` nor `dim_param` was present.
    Unknown,
}

impl fmt::Display for Dim {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Dim::Fixed(v) => write!(f, "{v}"),
            Dim::Param(p) => write!(f, "'{p}'"),
            Dim::Unknown => write!(f, "unknown"),
        }
    }
}

/// Name, element type, and shape of one graph input or output.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TensorSpec {
    /// Tensor name as declared in the graph.
    pub name: String,
    /// ONNX `TensorProto.DataType` code (1 = float32).
    pub elem_type: i32,
    /// Declared dimensions, outermost first.
    pub dims: Vec<Dim>,
    /// Whether a `TensorShapeProto` was present at all (an absent shape is
    /// distinct from a rank-0 shape).
    pub has_shape: bool,
}

/// One entry of `ModelProto.opset_import`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpsetId {
    /// Operator-set domain (`""` is the default ONNX domain).
    pub domain: String,
    /// Operator-set version.
    pub version: i64,
}

/// Summary of one graph initializer (weight or constant tensor).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InitializerSpec {
    /// Initializer name.
    pub name: String,
    /// ONNX `TensorProto.DataType` code.
    pub data_type: i32,
    /// Declared extents.
    pub dims: Vec<i64>,
    /// Whether the tensor payload lives in a companion `.onnx.data` file.
    pub external: bool,
}

/// The subset of `ModelProto` needed to validate a controller graph.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OnnxModelInfo {
    /// `ModelProto.ir_version`.
    pub ir_version: i64,
    /// `ModelProto.producer_name`.
    pub producer_name: String,
    /// `ModelProto.producer_version`.
    pub producer_version: String,
    /// `ModelProto.opset_import`, in file order.
    pub opset_import: Vec<OpsetId>,
    /// `GraphProto.name`.
    pub graph_name: String,
    /// `GraphProto.input`, in file order.
    pub inputs: Vec<TensorSpec>,
    /// `GraphProto.output`, in file order.
    pub outputs: Vec<TensorSpec>,
    /// `NodeProto.op_type` for every node, in file order.
    pub op_types: Vec<String>,
    /// `GraphProto.initializer`, in file order.
    pub initializers: Vec<InitializerSpec>,
    /// Distinct `external_data["location"]` values, in first-seen order.
    pub external_data_files: Vec<String>,
}

impl OnnxModelInfo {
    /// Version of the default (`""`) operator-set domain, if declared.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::onnx::inspect_onnx_bytes;
    ///
    /// // ir_version = 10; opset_import { version: 18 }; empty graph.
    /// let bytes = [0x08, 0x0a, 0x42, 0x02, 0x10, 0x12, 0x3a, 0x00];
    /// let info = inspect_onnx_bytes(&bytes)?;
    /// assert_eq!(info.default_opset(), Some(18));
    /// # Ok::<(), prin_daemon::DaemonError>(())
    /// ```
    #[must_use]
    pub fn default_opset(&self) -> Option<i64> {
        self.opset_import
            .iter()
            .find(|o| o.domain.is_empty())
            .map(|o| o.version)
    }
}

// ---------------------------------------------------------------------------
// Protobuf wire reader
// ---------------------------------------------------------------------------

/// A bounds-checked cursor over one protobuf message body.
struct Cursor<'a> {
    buf: &'a [u8],
    pos: usize,
    /// Offset of `buf[0]` within the whole file, for error reporting.
    base: usize,
}

impl<'a> Cursor<'a> {
    fn new(buf: &'a [u8], base: usize) -> Self {
        Self { buf, pos: 0, base }
    }

    fn offset(&self) -> usize {
        self.base.saturating_add(self.pos)
    }

    fn is_empty(&self) -> bool {
        self.pos >= self.buf.len()
    }

    fn err(&self, reason: &'static str) -> DaemonError {
        DaemonError::MalformedOnnx {
            offset: self.offset(),
            reason,
        }
    }

    fn read_varint(&mut self) -> Result<u64, DaemonError> {
        let mut value: u64 = 0;
        for shift in 0..10u32 {
            let byte = *self
                .buf
                .get(self.pos)
                .ok_or_else(|| self.err("truncated varint"))?;
            self.pos += 1;
            value |= u64::from(byte & 0x7f) << (shift * 7);
            if byte & 0x80 == 0 {
                return Ok(value);
            }
        }
        Err(self.err("varint longer than 10 bytes"))
    }

    fn read_bytes(&mut self, len: usize) -> Result<&'a [u8], DaemonError> {
        let end = self
            .pos
            .checked_add(len)
            .ok_or_else(|| self.err("length overflow"))?;
        let slice = self
            .buf
            .get(self.pos..end)
            .ok_or_else(|| self.err("truncated length-delimited field"))?;
        self.pos = end;
        Ok(slice)
    }

    fn read_tag(&mut self) -> Result<(u32, u8), DaemonError> {
        let key = self.read_varint()?;
        let wire = u8::try_from(key & 0x7).unwrap_or(u8::MAX);
        let field = u32::try_from(key >> 3).map_err(|_| self.err("field number overflow"))?;
        if field == 0 {
            return Err(self.err("field number 0 is reserved"));
        }
        Ok((field, wire))
    }

    /// Read a nested length-delimited message as its own cursor.
    fn read_message(&mut self) -> Result<Cursor<'a>, DaemonError> {
        let len = self.read_varint()?;
        let len = usize::try_from(len).map_err(|_| self.err("message length overflow"))?;
        let base = self.offset();
        Ok(Cursor::new(self.read_bytes(len)?, base))
    }

    fn read_string(&mut self) -> Result<String, DaemonError> {
        let len = self.read_varint()?;
        let len = usize::try_from(len).map_err(|_| self.err("string length overflow"))?;
        let raw = self.read_bytes(len)?;
        String::from_utf8(raw.to_vec()).map_err(|_| DaemonError::MalformedOnnx {
            offset: self.offset(),
            reason: "string field is not valid UTF-8",
        })
    }

    /// Skip a field of the given wire type without interpreting it.
    fn skip(&mut self, wire: u8) -> Result<(), DaemonError> {
        match wire {
            WIRE_VARINT => {
                self.read_varint()?;
            }
            WIRE_I64 => {
                self.read_bytes(8)?;
            }
            WIRE_LEN => {
                let len = self.read_varint()?;
                let len = usize::try_from(len).map_err(|_| self.err("length overflow"))?;
                self.read_bytes(len)?;
            }
            WIRE_I32 => {
                self.read_bytes(4)?;
            }
            _ => return Err(self.err("unsupported protobuf wire type")),
        }
        Ok(())
    }
}

/// Reinterpret a protobuf varint as a two's-complement `i64`.
fn as_i64(value: u64) -> i64 {
    i64::from_ne_bytes(value.to_ne_bytes())
}

/// Reinterpret a protobuf varint as a two's-complement `i32` (protobuf encodes
/// negative `int32` values as 10-byte sign-extended varints).
fn as_i32(value: u64) -> i32 {
    as_i64(value) as i32
}

// ---------------------------------------------------------------------------
// Message decoders
// ---------------------------------------------------------------------------

fn read_dimension(cur: &mut Cursor<'_>) -> Result<Dim, DaemonError> {
    let mut dim = Dim::Unknown;
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_VARINT) => dim = Dim::Fixed(as_i64(cur.read_varint()?)),
            (2, WIRE_LEN) => dim = Dim::Param(cur.read_string()?),
            _ => cur.skip(wire)?,
        }
    }
    Ok(dim)
}

fn read_shape(cur: &mut Cursor<'_>) -> Result<Vec<Dim>, DaemonError> {
    let mut dims = Vec::new();
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        if (field, wire) == (1, WIRE_LEN) {
            let mut nested = cur.read_message()?;
            dims.push(read_dimension(&mut nested)?);
        } else {
            cur.skip(wire)?;
        }
    }
    Ok(dims)
}

/// Decode `TypeProto.Tensor`, returning `(elem_type, shape)`.
fn read_tensor_type(cur: &mut Cursor<'_>) -> Result<(i32, Option<Vec<Dim>>), DaemonError> {
    let mut elem_type = 0;
    let mut shape = None;
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_VARINT) => elem_type = as_i32(cur.read_varint()?),
            (2, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                shape = Some(read_shape(&mut nested)?);
            }
            _ => cur.skip(wire)?,
        }
    }
    Ok((elem_type, shape))
}

/// Decode `TypeProto`, reading only the `tensor_type` variant.
fn read_type(cur: &mut Cursor<'_>) -> Result<(i32, Option<Vec<Dim>>), DaemonError> {
    let mut result = (0, None);
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        if (field, wire) == (1, WIRE_LEN) {
            let mut nested = cur.read_message()?;
            result = read_tensor_type(&mut nested)?;
        } else {
            cur.skip(wire)?;
        }
    }
    Ok(result)
}

fn read_value_info(cur: &mut Cursor<'_>) -> Result<TensorSpec, DaemonError> {
    let mut name = String::new();
    let mut elem_type = 0;
    let mut shape = None;
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_LEN) => name = cur.read_string()?,
            (2, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                let (et, sh) = read_type(&mut nested)?;
                elem_type = et;
                shape = sh;
            }
            _ => cur.skip(wire)?,
        }
    }
    Ok(TensorSpec {
        name,
        elem_type,
        has_shape: shape.is_some(),
        dims: shape.unwrap_or_default(),
    })
}

fn read_string_entry(cur: &mut Cursor<'_>) -> Result<(String, String), DaemonError> {
    let mut key = String::new();
    let mut value = String::new();
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_LEN) => key = cur.read_string()?,
            (2, WIRE_LEN) => value = cur.read_string()?,
            _ => cur.skip(wire)?,
        }
    }
    Ok((key, value))
}

fn read_initializer(
    cur: &mut Cursor<'_>,
    external_files: &mut Vec<String>,
) -> Result<InitializerSpec, DaemonError> {
    let mut name = String::new();
    let mut data_type = 0;
    let mut dims = Vec::new();
    let mut location = None;
    let mut external = false;
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_VARINT) => dims.push(as_i64(cur.read_varint()?)),
            (1, WIRE_LEN) => {
                // Packed `dims`.
                let mut packed = cur.read_message()?;
                while !packed.is_empty() {
                    dims.push(as_i64(packed.read_varint()?));
                }
            }
            (2, WIRE_VARINT) => data_type = as_i32(cur.read_varint()?),
            (8, WIRE_LEN) => name = cur.read_string()?,
            (13, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                let (key, value) = read_string_entry(&mut nested)?;
                if key == "location" {
                    location = Some(value);
                }
            }
            (14, WIRE_VARINT) => external = as_i64(cur.read_varint()?) == DATA_LOCATION_EXTERNAL,
            _ => cur.skip(wire)?,
        }
    }
    if external {
        if let Some(file) = location {
            if !external_files.contains(&file) {
                external_files.push(file);
            }
        }
    }
    Ok(InitializerSpec {
        name,
        data_type,
        dims,
        external,
    })
}

fn read_node_op_type(cur: &mut Cursor<'_>) -> Result<String, DaemonError> {
    let mut op_type = String::new();
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        if (field, wire) == (4, WIRE_LEN) {
            op_type = cur.read_string()?;
        } else {
            cur.skip(wire)?;
        }
    }
    Ok(op_type)
}

/// Decoded `GraphProto` fields.
struct GraphParts {
    name: String,
    inputs: Vec<TensorSpec>,
    outputs: Vec<TensorSpec>,
    op_types: Vec<String>,
    initializers: Vec<InitializerSpec>,
    external_data_files: Vec<String>,
}

fn read_graph(cur: &mut Cursor<'_>) -> Result<GraphParts, DaemonError> {
    let mut parts = GraphParts {
        name: String::new(),
        inputs: Vec::new(),
        outputs: Vec::new(),
        op_types: Vec::new(),
        initializers: Vec::new(),
        external_data_files: Vec::new(),
    };
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                parts.op_types.push(read_node_op_type(&mut nested)?);
            }
            (2, WIRE_LEN) => parts.name = cur.read_string()?,
            (5, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                let init = read_initializer(&mut nested, &mut parts.external_data_files)?;
                parts.initializers.push(init);
            }
            (11, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                parts.inputs.push(read_value_info(&mut nested)?);
            }
            (12, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                parts.outputs.push(read_value_info(&mut nested)?);
            }
            _ => cur.skip(wire)?,
        }
    }
    Ok(parts)
}

fn read_opset_id(cur: &mut Cursor<'_>) -> Result<OpsetId, DaemonError> {
    let mut domain = String::new();
    let mut version = 0;
    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_LEN) => domain = cur.read_string()?,
            (2, WIRE_VARINT) => version = as_i64(cur.read_varint()?),
            _ => cur.skip(wire)?,
        }
    }
    Ok(OpsetId { domain, version })
}

/// Decode the controller-relevant fields of a serialized `ModelProto`.
///
/// # Errors
///
/// Returns [`DaemonError::MalformedOnnx`] if the byte stream is not a
/// well-formed protobuf message, contains a non-UTF-8 string field, uses an
/// unsupported wire type, or declares no `graph`.
///
/// # Examples
///
/// ```
/// use prin_daemon::onnx::inspect_onnx_bytes;
///
/// // Field 1 (`ir_version`) = 10, then field 7 (`graph`) = empty message.
/// let bytes = [0x08, 0x0a, 0x3a, 0x00];
/// let info = inspect_onnx_bytes(&bytes)?;
/// assert_eq!(info.ir_version, 10);
/// assert!(info.inputs.is_empty());
/// # Ok::<(), prin_daemon::DaemonError>(())
/// ```
pub fn inspect_onnx_bytes(bytes: &[u8]) -> Result<OnnxModelInfo, DaemonError> {
    let mut cur = Cursor::new(bytes, 0);
    let mut ir_version = 0;
    let mut producer_name = String::new();
    let mut producer_version = String::new();
    let mut opset_import = Vec::new();
    let mut graph: Option<GraphParts> = None;

    while !cur.is_empty() {
        let (field, wire) = cur.read_tag()?;
        match (field, wire) {
            (1, WIRE_VARINT) => ir_version = as_i64(cur.read_varint()?),
            (2, WIRE_LEN) => producer_name = cur.read_string()?,
            (3, WIRE_LEN) => producer_version = cur.read_string()?,
            (7, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                graph = Some(read_graph(&mut nested)?);
            }
            (8, WIRE_LEN) => {
                let mut nested = cur.read_message()?;
                opset_import.push(read_opset_id(&mut nested)?);
            }
            _ => cur.skip(wire)?,
        }
    }

    let graph = graph.ok_or(DaemonError::MalformedOnnx {
        offset: bytes.len(),
        reason: "ModelProto has no `graph` field",
    })?;

    Ok(OnnxModelInfo {
        ir_version,
        producer_name,
        producer_version,
        opset_import,
        graph_name: graph.name,
        inputs: graph.inputs,
        outputs: graph.outputs,
        op_types: graph.op_types,
        initializers: graph.initializers,
        external_data_files: graph.external_data_files,
    })
}

/// Read and decode an ONNX model file.
///
/// # Errors
///
/// Returns [`DaemonError::Io`] if the file cannot be read, or
/// [`DaemonError::MalformedOnnx`] if its contents are not a decodable
/// `ModelProto`.
pub fn inspect_onnx_file(path: impl AsRef<Path>) -> Result<OnnxModelInfo, DaemonError> {
    let path = path.as_ref();
    let bytes = std::fs::read(path).map_err(|source| DaemonError::Io {
        path: path.display().to_string(),
        source,
    })?;
    inspect_onnx_bytes(&bytes)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Encode a protobuf tag for `(field, wire)` as a varint.
    fn tag(field: u32, wire: u8) -> Vec<u8> {
        varint((u64::from(field) << 3) | u64::from(wire))
    }

    /// Wrap `body` as a length-delimited field.
    fn len_field(field: u32, body: &[u8]) -> Vec<u8> {
        let mut out = tag(field, WIRE_LEN);
        out.extend(varint(body.len() as u64));
        out.extend_from_slice(body);
        out
    }

    fn varint(mut value: u64) -> Vec<u8> {
        let mut out = Vec::new();
        loop {
            let byte = u8::try_from(value & 0x7f).expect("masked");
            value >>= 7;
            if value == 0 {
                out.push(byte);
                return out;
            }
            out.push(byte | 0x80);
        }
    }

    fn varint_field(field: u32, value: u64) -> Vec<u8> {
        let mut out = tag(field, WIRE_VARINT);
        out.extend(varint(value));
        out
    }

    fn string_field(field: u32, value: &str) -> Vec<u8> {
        len_field(field, value.as_bytes())
    }

    /// Build a `ValueInfoProto` with a 2-D `[batch, extent]` float shape.
    fn value_info(name: &str, extent: i64) -> Vec<u8> {
        let mut dim_batch = Vec::new();
        dim_batch.extend(string_field(2, "batch"));
        let mut dim_fixed = Vec::new();
        dim_fixed.extend(varint_field(1, extent as u64));

        let mut shape = Vec::new();
        shape.extend(len_field(1, &dim_batch));
        shape.extend(len_field(1, &dim_fixed));

        let mut tensor_type = Vec::new();
        tensor_type.extend(varint_field(1, ELEM_TYPE_FLOAT as u64));
        tensor_type.extend(len_field(2, &shape));

        let type_proto = len_field(1, &tensor_type);

        let mut vi = Vec::new();
        vi.extend(string_field(1, name));
        vi.extend(len_field(2, &type_proto));
        vi
    }

    /// Build a minimal controller-shaped `ModelProto`.
    fn controller_model() -> Vec<u8> {
        let mut graph = Vec::new();
        graph.extend(string_field(2, "main_graph"));
        graph.extend(len_field(1, &string_field(4, "Gemm")));
        graph.extend(len_field(11, &value_info("state_vector", 32)));
        graph.extend(len_field(12, &value_info("control_signals", 8)));

        let mut opset = Vec::new();
        opset.extend(varint_field(2, 18));

        let mut model = Vec::new();
        model.extend(varint_field(1, 10));
        model.extend(string_field(2, "pytorch"));
        model.extend(string_field(3, "2.10.0"));
        model.extend(len_field(7, &graph));
        model.extend(len_field(8, &opset));
        model
    }

    #[test]
    fn decodes_controller_shaped_model() {
        let info = inspect_onnx_bytes(&controller_model()).expect("decodes");
        assert_eq!(info.ir_version, 10);
        assert_eq!(info.producer_name, "pytorch");
        assert_eq!(info.producer_version, "2.10.0");
        assert_eq!(info.graph_name, "main_graph");
        assert_eq!(info.default_opset(), Some(18));
        assert_eq!(info.op_types, vec!["Gemm".to_string()]);
        assert_eq!(info.inputs.len(), 1);
        assert_eq!(info.inputs[0].name, "state_vector");
        assert_eq!(info.inputs[0].elem_type, ELEM_TYPE_FLOAT);
        assert!(info.inputs[0].has_shape);
        assert_eq!(
            info.inputs[0].dims,
            vec![Dim::Param("batch".to_string()), Dim::Fixed(32)]
        );
        assert_eq!(info.outputs[0].name, "control_signals");
        assert_eq!(
            info.outputs[0].dims,
            vec![Dim::Param("batch".to_string()), Dim::Fixed(8)]
        );
    }

    #[test]
    fn unknown_fields_of_every_wire_type_are_skipped() {
        let mut model = controller_model();
        // Unknown varint, 64-bit, length-delimited, and 32-bit fields.
        model.extend(varint_field(1000, 7));
        model.extend(tag(1001, WIRE_I64));
        model.extend_from_slice(&[0u8; 8]);
        model.extend(len_field(1002, b"opaque"));
        model.extend(tag(1003, WIRE_I32));
        model.extend_from_slice(&[0u8; 4]);
        let info = inspect_onnx_bytes(&model).expect("skips unknown fields");
        assert_eq!(info.graph_name, "main_graph");
    }

    #[test]
    fn unknown_fields_inside_every_nested_message_are_skipped() {
        // Real exports carry `denotation`, `doc_string`, and `metadata_props`
        // in exactly these positions; each must be stepped over by wire type
        // without disturbing the fields the controller contract needs.
        let mut dim_batch = Vec::new();
        dim_batch.extend(string_field(2, "batch"));
        dim_batch.extend(string_field(3, "DATA_BATCH")); // Dimension.denotation
        let mut dim_fixed = Vec::new();
        dim_fixed.extend(varint_field(1, 32));
        dim_fixed.extend(varint_field(99, 1)); // unknown varint in Dimension

        let mut shape = Vec::new();
        shape.extend(len_field(1, &dim_batch));
        shape.extend(len_field(1, &dim_fixed));
        shape.extend(len_field(77, b"unknown-in-shape"));

        let mut tensor_type = Vec::new();
        tensor_type.extend(varint_field(1, ELEM_TYPE_FLOAT as u64));
        tensor_type.extend(len_field(2, &shape));
        tensor_type.extend(varint_field(64, 3)); // unknown in TypeProto.Tensor

        let mut type_proto = Vec::new();
        type_proto.extend(len_field(1, &tensor_type));
        type_proto.extend(string_field(6, "TENSOR")); // TypeProto.denotation

        let mut vi = Vec::new();
        vi.extend(string_field(1, "state_vector"));
        vi.extend(len_field(2, &type_proto));
        vi.extend(string_field(3, "the state vector")); // doc_string

        let mut entry = Vec::new();
        entry.extend(string_field(1, "location"));
        entry.extend(string_field(2, "weights.onnx.data"));
        entry.extend(varint_field(9, 1)); // unknown in StringStringEntryProto

        let mut init = Vec::new();
        init.extend(string_field(8, "net.0.weight"));
        init.extend(varint_field(14, DATA_LOCATION_EXTERNAL as u64));
        init.extend(len_field(13, &entry));
        init.extend(string_field(12, "doc")); // TensorProto.doc_string

        let mut node = Vec::new();
        node.extend(string_field(3, "node_Gemm_0")); // NodeProto.name
        node.extend(string_field(4, "Gemm"));

        let mut opset = Vec::new();
        opset.extend(varint_field(2, 18));
        opset.extend(string_field(9, "unknown-in-opset"));

        let mut graph = Vec::new();
        graph.extend(string_field(2, "main_graph"));
        graph.extend(len_field(1, &node));
        graph.extend(len_field(5, &init));
        graph.extend(len_field(11, &vi));
        graph.extend(string_field(10, "graph doc")); // GraphProto.doc_string

        let mut model = Vec::new();
        model.extend(varint_field(1, 10));
        model.extend(len_field(7, &graph));
        model.extend(len_field(8, &opset));
        model.extend(varint_field(5, 7)); // ModelProto.model_version

        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert_eq!(info.graph_name, "main_graph");
        assert_eq!(info.default_opset(), Some(18));
        assert_eq!(info.op_types, vec!["Gemm".to_string()]);
        assert_eq!(info.inputs[0].name, "state_vector");
        assert_eq!(info.inputs[0].elem_type, ELEM_TYPE_FLOAT);
        assert_eq!(
            info.inputs[0].dims,
            vec![Dim::Param("batch".to_string()), Dim::Fixed(32)]
        );
        assert_eq!(
            info.external_data_files,
            vec!["weights.onnx.data".to_string()]
        );
        assert!(info.initializers[0].external);
    }

    #[test]
    fn an_external_tensor_without_a_location_adds_no_companion() {
        let mut entry = Vec::new();
        entry.extend(string_field(1, "offset"));
        entry.extend(string_field(2, "0"));
        let mut init = Vec::new();
        init.extend(string_field(8, "net.0.weight"));
        init.extend(varint_field(14, DATA_LOCATION_EXTERNAL as u64));
        init.extend(len_field(13, &entry));
        let graph = len_field(5, &init);
        let model = len_field(7, &graph);

        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert!(info.initializers[0].external);
        assert!(info.external_data_files.is_empty());
    }

    #[test]
    fn missing_graph_is_rejected() {
        let bytes = varint_field(1, 10);
        let err = inspect_onnx_bytes(&bytes).expect_err("no graph");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "ModelProto has no `graph` field",
                ..
            }
        ));
    }

    #[test]
    fn truncated_message_is_rejected() {
        let full = controller_model();
        let err = inspect_onnx_bytes(&full[..full.len() - 3]).expect_err("truncated");
        assert!(matches!(err, DaemonError::MalformedOnnx { .. }));
    }

    #[test]
    fn truncated_varint_is_rejected() {
        // A single continuation byte with no terminator.
        let err = inspect_onnx_bytes(&[0x80]).expect_err("truncated varint");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "truncated varint",
                ..
            }
        ));
    }

    #[test]
    fn overlong_varint_is_rejected() {
        let err = inspect_onnx_bytes(&[0x80; 11]).expect_err("overlong varint");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "varint longer than 10 bytes",
                ..
            }
        ));
    }

    #[test]
    fn an_absurd_field_length_cannot_overflow_the_cursor() {
        // A length-delimited field declaring `u64::MAX` bytes. The cursor must
        // reject it by arithmetic, never by wrapping or allocating.
        let mut bytes = tag(2, WIRE_LEN);
        bytes.extend(varint(u64::MAX));
        let err = inspect_onnx_bytes(&bytes).expect_err("absurd length");
        assert!(matches!(err, DaemonError::MalformedOnnx { .. }));

        // The same, in a field this reader skips rather than decodes.
        let mut skipped = tag(1000, WIRE_LEN);
        skipped.extend(varint(u64::MAX));
        let err = inspect_onnx_bytes(&skipped).expect_err("absurd skip length");
        assert!(matches!(err, DaemonError::MalformedOnnx { .. }));

        // And nested inside a graph, where a sub-cursor performs the read.
        let mut nested = tag(7, WIRE_LEN);
        nested.extend(varint(u64::MAX));
        let err = inspect_onnx_bytes(&nested).expect_err("absurd graph length");
        assert!(matches!(err, DaemonError::MalformedOnnx { .. }));
    }

    #[test]
    fn a_field_number_beyond_u32_is_rejected() {
        // Tag key with a field number that does not fit in `u32`.
        let bytes = varint(u64::MAX);
        let err = inspect_onnx_bytes(&bytes).expect_err("field number overflow");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "field number overflow",
                ..
            }
        ));
    }

    #[test]
    fn a_truncated_string_field_is_rejected() {
        // `producer_name` declares eight bytes but only three follow.
        let mut bytes = tag(2, WIRE_LEN);
        bytes.extend(varint(8));
        bytes.extend_from_slice(b"abc");
        let err = inspect_onnx_bytes(&bytes).expect_err("truncated string");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "truncated length-delimited field",
                ..
            }
        ));
    }

    #[test]
    fn zero_field_number_is_rejected() {
        let err = inspect_onnx_bytes(&[0x00]).expect_err("field 0");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "field number 0 is reserved",
                ..
            }
        ));
    }

    #[test]
    fn group_wire_types_are_rejected() {
        // Wire type 3 (start-group) is not supported by proto3 or this reader.
        let err = inspect_onnx_bytes(&tag(1, 3)).expect_err("group wire type");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "unsupported protobuf wire type",
                ..
            }
        ));
    }

    #[test]
    fn non_utf8_string_is_rejected() {
        let mut model = tag(2, WIRE_LEN);
        model.extend_from_slice(&[2, 0xff, 0xfe]);
        model.extend(len_field(7, &[]));
        let err = inspect_onnx_bytes(&model).expect_err("bad utf-8");
        assert!(matches!(
            err,
            DaemonError::MalformedOnnx {
                reason: "string field is not valid UTF-8",
                ..
            }
        ));
    }

    #[test]
    fn dimension_without_value_or_param_is_unknown() {
        let shape = len_field(1, &[]);
        let mut tensor_type = Vec::new();
        tensor_type.extend(varint_field(1, ELEM_TYPE_FLOAT as u64));
        tensor_type.extend(len_field(2, &shape));
        let type_proto = len_field(1, &tensor_type);
        let mut vi = Vec::new();
        vi.extend(string_field(1, "x"));
        vi.extend(len_field(2, &type_proto));

        let mut graph = Vec::new();
        graph.extend(len_field(11, &vi));
        let mut model = Vec::new();
        model.extend(len_field(7, &graph));

        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert_eq!(info.inputs[0].dims, vec![Dim::Unknown]);
    }

    #[test]
    fn value_info_without_type_has_no_shape() {
        let vi = string_field(1, "x");
        let graph = len_field(11, &vi);
        let model = len_field(7, &graph);
        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert!(!info.inputs[0].has_shape);
        assert!(info.inputs[0].dims.is_empty());
        assert_eq!(info.inputs[0].elem_type, 0);
    }

    #[test]
    fn packed_and_unpacked_initializer_dims_are_both_read() {
        let mut unpacked = Vec::new();
        unpacked.extend(varint_field(1, 128));
        unpacked.extend(varint_field(1, 32));
        unpacked.extend(varint_field(2, ELEM_TYPE_FLOAT as u64));
        unpacked.extend(string_field(8, "net.0.weight"));
        unpacked.extend(varint_field(14, DATA_LOCATION_EXTERNAL as u64));
        let mut entry = Vec::new();
        entry.extend(string_field(1, "location"));
        entry.extend(string_field(2, "model.onnx.data"));
        unpacked.extend(len_field(13, &entry));

        let mut packed_dims = Vec::new();
        packed_dims.extend(varint(8));
        packed_dims.extend(varint(128));
        let mut packed = Vec::new();
        packed.extend(len_field(1, &packed_dims));
        packed.extend(string_field(8, "net.6.weight"));

        let mut graph = Vec::new();
        graph.extend(len_field(5, &unpacked));
        graph.extend(len_field(5, &packed));
        let model = len_field(7, &graph);

        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert_eq!(info.initializers[0].dims, vec![128, 32]);
        assert!(info.initializers[0].external);
        assert_eq!(info.initializers[1].dims, vec![8, 128]);
        assert!(!info.initializers[1].external);
        assert_eq!(
            info.external_data_files,
            vec!["model.onnx.data".to_string()]
        );
    }

    #[test]
    fn repeated_external_locations_are_deduplicated() {
        let make = |name: &str| {
            let mut entry = Vec::new();
            entry.extend(string_field(1, "location"));
            entry.extend(string_field(2, "model.onnx.data"));
            let mut init = Vec::new();
            init.extend(string_field(8, name));
            init.extend(varint_field(14, DATA_LOCATION_EXTERNAL as u64));
            init.extend(len_field(13, &entry));
            init
        };
        let mut graph = Vec::new();
        graph.extend(len_field(5, &make("a")));
        graph.extend(len_field(5, &make("b")));
        let model = len_field(7, &graph);
        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert_eq!(info.external_data_files.len(), 1);
    }

    #[test]
    fn negative_elem_type_round_trips_as_i32() {
        // proto3 encodes negative int32 as a 10-byte sign-extended varint.
        let mut tensor_type = Vec::new();
        tensor_type.extend(varint_field(1, (-1i64) as u64));
        let type_proto = len_field(1, &tensor_type);
        let mut vi = Vec::new();
        vi.extend(string_field(1, "x"));
        vi.extend(len_field(2, &type_proto));
        let graph = len_field(11, &vi);
        let model = len_field(7, &graph);
        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert_eq!(info.inputs[0].elem_type, -1);
    }

    #[test]
    fn opset_domain_is_recorded_and_non_default_ignored_by_default_opset() {
        let mut custom = Vec::new();
        custom.extend(string_field(1, "com.microsoft"));
        custom.extend(varint_field(2, 1));
        let mut model = Vec::new();
        model.extend(len_field(8, &custom));
        model.extend(len_field(7, &[]));
        let info = inspect_onnx_bytes(&model).expect("decodes");
        assert_eq!(info.default_opset(), None);
        assert_eq!(info.opset_import[0].domain, "com.microsoft");
        assert_eq!(info.opset_import[0].version, 1);
    }

    #[test]
    fn dim_display_covers_every_variant() {
        assert_eq!(Dim::Fixed(32).to_string(), "32");
        assert_eq!(Dim::Param("batch".to_string()).to_string(), "'batch'");
        assert_eq!(Dim::Unknown.to_string(), "unknown");
    }

    #[test]
    fn missing_file_reports_io_error() {
        let err = inspect_onnx_file("this-file-does-not-exist.onnx").expect_err("missing");
        assert!(matches!(err, DaemonError::Io { .. }));
    }
}
