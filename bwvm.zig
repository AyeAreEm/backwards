const std = @import("std");

pub fn Dyn(comptime T: type) type {
    return struct {
        data: []T,
        len: usize,
        cap: usize,
        allocator: std.mem.Allocator,

        pub fn init(allocator: std.mem.Allocator) !Dyn(T) {
            var arr: Dyn(T) = undefined;
            arr.len = 0;
            arr.cap = 32;
            arr.allocator = allocator;
            arr.data = try allocator.alloc(T, arr.cap);
            return arr;
        }

        pub fn withCapacity(allocator: std.mem.Allocator, cap: usize) !Dyn(T) {
            var arr: Dyn(T) = undefined;
            arr.len = 0;
            arr.cap = cap;
            arr.allocator = allocator;
            arr.data = try allocator.alloc(T, arr.cap);
            return arr;
        }

        pub fn dupe(self: *Dyn(T)) !Dyn(T) {
            const new_buf = try self.allocator.dupe(T, self.data);
            return Dyn(T){
                .len = self.len,
                .cap = self.cap,
                .allocator = self.allocator,
                .data = new_buf,
            };
        }

        pub fn at(self: *Dyn(T), index: usize) ?T {
            if (index >= self.len) {
                return null;
            }

            return self.data[index];
        }

        pub fn resize(self: *Dyn(T)) !void {
            self.cap *= 2;
            self.data = try self.allocator.realloc(self.data, self.cap * @sizeOf(T));
        }

        pub fn resizeWithSize(self: *Dyn(T), size: usize) !void {
            self.cap = (self.cap * 2) + size;
            self.data = try self.allocator.realloc(self.data, self.cap * @sizeOf(T));
        }

        pub fn push(self: *Dyn(T), elem: T) !void {
            if (self.len + 1 >= self.cap) {
                try self.resize();
            }

            self.data[self.len] = elem;
            self.len += 1;
        }

        pub fn pop(self: *Dyn(T)) ?T {
            if (self.len == 0) {
                return null;
            }

            const elem = self.at(self.len - 1);
            if (elem) |_| {
                self.len -= 1;
            }

            return elem;
        }

        pub fn replace(self: *Dyn(T), index: usize, elem: T) !void {
            if (index >= self.len) {
                return error.IndexOutOfBounds;
            }

            self.data[index] = elem;
        }

        pub fn clear(self: *Dyn(T)) void {
            self.len = 0;
            self.data[0] = 0;
        }

        pub fn remove(self: *Dyn(T), index: usize) !T {
            const result = self.at(0) orelse return error.IndexOutOfBounds;

            for (index + 1..self.len) |i| {
                self.data[i - 1] = self.data[i];
            }
            self.len -= 1;

            return result;
        }

        pub fn deinit(self: *Dyn(T)) void {
            self.len = 0;
            self.cap = 0;
            self.allocator.free(self.data);
        }
    };
}

pub const String = struct {
    buf: Dyn(u8),

    pub fn init(allocator: std.mem.Allocator) !String {
        return String{ .buf = try Dyn(u8).init(allocator) };
    }

    pub fn withCapacity(allocator: std.mem.Allocator, cap: usize) !String {
        return String{ .buf = try Dyn(u8).withCapacity(allocator, cap) };
    }

    pub fn dupe(self: *String) !String {
        var new_str = String{ .buf = self.buf.dupe() };

        if (new_str.buf.len + 1 >= new_str.buf.cap) {
            try new_str.buf.resize();
        }

        new_str.buf.data[new_str.buf.len] = 0;
        return new_str;
    }

    pub fn from(content: []const u8, allocator: std.mem.Allocator) !String {
        var str: String = try String.init(allocator);
        for (content) |ch| {
            try str.buf.push(ch);
        }

        if (str.buf.len + 1 >= str.buf.cap) {
            try str.buf.resize();
        }

        str.buf.data[str.buf.len] = 0;
        return str;
    }

    pub fn at(self: *String, index: usize) ?u8 {
        return self.buf.at(index);
    }

    pub fn pushChar(self: *String, ch: u8) !void {
        if (self.buf.len + 1 >= self.buf.cap) {
            try self.buf.resize();
        }

        self.buf.data[self.buf.len] = ch;
        self.buf.len += 1;
        self.buf.data[self.buf.len] = 0;
    }

    pub fn pushSlice(self: *String, content: []const u8) !void {
        if (self.buf.len + content.len >= self.buf.cap) {
            try self.buf.resizeWithSize(content.len);
        }

        for (content) |ch| {
            try self.pushChar(ch);
        }
    }

    pub fn pushString(self: *String, content: String) !void {
        try self.pushSlice(content.getSlice());
    }

    pub fn push(self: *String, elem: anytype) !void {
        switch (@TypeOf(elem)) {
            comptime_int => {
                // const char: u8 = @intCast(elem);
                // try self.pushChar(char);
                try self.pushChar(elem);
            },
            []const u8 => {
                try self.pushSlice(elem);
            },
            String => {
                try self.pushString(elem);
            },
            else => {
                const slice = if (@typeInfo(@TypeOf(elem)) == .Pointer) elem else &elem;
                try self.pushSlice(slice);
            },
        }
    }

    pub fn pop(self: *String) ?u8 {
        return self.buf.pop();
    }

    pub fn replace(self: *String, index: usize, ch: u8) !void {
        try self.buf.replace(index, ch);
    }

    pub fn containsChar(self: *String, pattern: u8) struct { bool, usize } {
        for (0..self.buf.len) |i| {
            if (self.buf.data[i] == pattern) {
                return .{ true, i };
            }
        }

        return .{ false, 0 };
    }

    pub fn containsSlice(self: *String, pattern: []const u8) struct { bool, usize } {
        var head: usize = 0;
        var index: usize = 0;

        if (self.buf.len < pattern.len) {
            return .{ false, 0 };
        }

        for (0..self.buf.len) |i| {
            if (head == pattern.len) {
                return .{ true, index };
            }

            if (self.buf.data[i] == pattern[head]) {
                head += 1;
            } else {
                head = 0;
                if (i == 0) {
                    index = 1;
                } else {
                    index = i;
                }
            }
        }

        if (head == pattern.len) {
            return .{ true, index };
        }

        return .{ false, 0 };
    }

    pub fn containsString(self: *String, pattern: String) struct { bool, usize } {
        return self.containsSlice(pattern.getSlice());
    }

    pub fn contains(self: *String, pattern: anytype) !struct { bool, usize } {
        switch (@TypeOf(pattern)) {
            comptime_int => {
                return self.containsChar(pattern);
            },
            []const u8 => {
                return self.containsSlice(pattern);
            },
            String => {
                return self.containsString(pattern);
            },
            else => {
                const slice = if (@typeInfo(@TypeOf(pattern)) == .Pointer) pattern else &pattern;
                return self.containsSlice(slice);
            },
        }
    }

    pub fn compareSlice(self: *String, comparate: []const u8) bool {
        if (self.buf.len != comparate.len) {
            return false;
        }

        for (comparate, 0..) |ch, i| {
            if (self.buf.data[i] != ch) {
                return false;
            }
        }

        return true;
    }

    pub fn compareString(self: *String, comparate: String) bool {
        return self.compareSlice(comparate.getSlice());
    }

    pub fn compare(self: *String, comparate: anytype) !bool {
        switch (@TypeOf(comparate)) {
            []const u8 => {
                return self.compareSlice(comparate);
            },
            String => {
                return self.compareString(comparate);
            },
            else => {
                const slice = if (@typeInfo(@TypeOf(comparate)) == .Pointer) comparate else &comparate;
                return self.compareSlice(slice);
            },
        }
    }

    pub fn startsWith(self: *String, pattern: u8) bool {
        if (self.at(0)) |ch| {
            return ch == pattern;
        }

        return false;
    }

    pub fn endsWith(self: *String, pattern: u8) bool {
        if (self.at(self.buf.len - 1)) |ch| {
            return ch == pattern;
        }

        return false;
    }

    pub fn toUppercase(self: *String) void {
        self.buf.data = std.ascii.upperString(self.buf.data, self.buf.data);
    }

    pub fn toLowercase(self: *String) void {
        self.buf.data = std.ascii.lowerString(self.buf.data, self.buf.data);
    }

    pub fn getSlice(self: *String) []const u8 {
        return self.buf.data[0..self.buf.len];
    }

    pub fn getMutSlice(self: *String) []u8 {
        return self.buf.data[self.buf.head..self.buf.len];
    }

    pub fn clear(self: *String) void {
        self.buf.clear();
    }

    pub fn deinit(self: *String) void {
        self.buf.deinit();
    }
};

const Type = enum {
    I128,
    U128,
};

const TypeInfo = struct {
    size: usize,
    alignment: usize,
    typ: Type,

    pub fn from_str(buf: []const u8) struct { TypeInfo, usize } {
        if (std.mem.eql(u8, buf[0..4], "i128")) {
            return .{ TypeInfo{ .size = 16, .alignment = 16, .typ = .I128 }, 4 };
        } else if (std.mem.eql(u8, buf[0..4], "u128")) {
            return .{ TypeInfo{ .size = 16, .alignment = 16, .typ = .U128 }, 4 };
        }

        // TODO: change this to not bug out when there's more types
        unreachable;
    }
};

const Opcode = union(enum) {
    Return: TypeInfo,
    Print: TypeInfo,
    Push: u128,
    Add: TypeInfo,
    Sub: TypeInfo,
    Mul: TypeInfo,
    Div: TypeInfo,
    Set: usize,
    Get: usize,

    pub fn handle_typed_op(op: []const u8, optype: TypeInfo, rest: []const u8) Opcode {
        _ = rest;

        if (std.mem.eql(u8, op, "add")) {
            return Opcode{ .Add = optype };
        } else if (std.mem.eql(u8, op, "sub")) {
            return Opcode{ .Sub = optype };
        } else if (std.mem.eql(u8, op, "mul")) {
            return Opcode{ .Mul = optype };
        } else if (std.mem.eql(u8, op, "div")) {
            return Opcode{ .Div = optype };
        } else if (std.mem.eql(u8, op, "ret")) {
            return Opcode{ .Return = optype };
        } else if (std.mem.eql(u8, op, "print")) {
            return Opcode{ .Print = optype };
        }
        std.debug.print("op: {s}\n", .{op});
        unreachable;
    }

    pub fn handle_untyped_op(op: []const u8, rest: []const u8) Opcode {
        if (std.mem.eql(u8, op, "push")) {
            const num: ?u128 = std.fmt.parseUnsigned(u128, rest, 0) catch null;
            if (num) |value| {
                return Opcode{ .Push = value };
            }

            std.debug.panic("expected to push hex value, got {s}", .{rest});
        } else if (std.mem.eql(u8, op, "set")) {
            const index = std.fmt.parseInt(u8, rest, 10) catch null;
            if (index) |i| {
                return Opcode{ .Set = i };
            }

            std.debug.panic("failed to parse memory location during set opcode", .{});
        } else if (std.mem.eql(u8, op, "get")) {
            const index = std.fmt.parseInt(u8, rest, 10) catch null;
            if (index) |i| {
                return Opcode{ .Get = i };
            }

            std.debug.panic("failed to parse memory location during get opcode", .{});
        }

        std.debug.print("op: {s}\n", .{op});
        unreachable;
    }

    pub fn get_op(buf: []const u8) !Opcode {
        // WARN: if opcode is bigger than 10 then lols doesn't work get fucked, make it bigger
        var op: [10]u8 = undefined;
        var op_end: usize = undefined;
        for (buf, 0..) |ch, i| {
            if (!std.ascii.isAlphabetic(ch)) {
                op_end = i;
                break;
            }

            op[i] = ch;
        }

        if (buf[op_end] == '.') {
            const optype = buf[op_end + 1 ..]; // TODO: watch this bad boy right here cuz he might either be a "" or error
            const info = TypeInfo.from_str(optype);
            return handle_typed_op(op[0..op_end], info[0], optype[info[1]..]);
        } else {
            return handle_untyped_op(op[0..op_end], buf[op_end + 1 ..]);
        }

        unreachable;
    }

    pub fn perform_op(typeinfo: TypeInfo, left: u128, op: fn (anytype, anytype) *anyopaque, right: u128) u128 {
        switch (typeinfo.typ) {
            .I128 => {
                const lhs: i128 = @bitCast(left);
                const rhs: i128 = @bitCast(right);
                return @as(*u128, @alignCast(@ptrCast(op(lhs, rhs)))).*;
            },
            .U128 => {
                return @as(*u128, @alignCast(@ptrCast(op(left, right)))).*;
            },
        }
    }

    pub fn add(left: anytype, right: anytype) *anyopaque {
        return @constCast(&(left + right));
    }

    pub fn sub(left: anytype, right: anytype) *anyopaque {
        return @constCast(&(left - right));
    }

    pub fn mul(left: anytype, right: anytype) *anyopaque {
        return @constCast(&(left * right));
    }

    pub fn div(left: anytype, right: anytype) *anyopaque {
        _ = left;
        _ = right;
        std.debug.panic("div not implemented yet", .{});
        // return @constCast(&(left / right));
    }

    pub fn print(left: anytype, right: anytype) *anyopaque {
        std.debug.print("{}\n", .{left});
        return @constCast(&(right));
    }
};

fn get_opcodes(line: []const u8) !Dyn(Opcode) {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();
    var opcodes = try Dyn(Opcode).init(allocator);

    var buf = try String.init(allocator);
    defer buf.deinit();

    for (line) |ch| {
        if (ch == '\n') {
            buf.toLowercase();
            try opcodes.push(try Opcode.get_op(buf.getSlice()));
            buf.clear();
        } else if (ch == '\r') {
            continue;
        } else {
            try buf.pushChar(ch);
        }
    }

    buf.toLowercase();
    try opcodes.push(try Opcode.get_op(buf.getSlice()));

    return opcodes;
}

fn interpret(line: []const u8, stack: *Dyn(u128), memory: *[]u8) !void {
    var opcodes = try get_opcodes(line);

    while (opcodes.at(0)) |opcode| {
        _ = try opcodes.remove(0);

        switch (opcode) {
            .Add => |typeinfo| {
                const right = stack.pop();
                const left = stack.pop();

                if (left) |lhs| {
                    if (right) |rhs| {
                        const value = Opcode.perform_op(typeinfo, lhs, Opcode.add, rhs);
                        try stack.push(value);
                        continue;
                    }
                }

                std.debug.panic("error: empty stack when doing addition\n", .{});
            },
            .Sub => |typeinfo| {
                const right = stack.pop();
                const left = stack.pop();

                if (left) |lhs| {
                    if (right) |rhs| {
                        const value = Opcode.perform_op(typeinfo, lhs, Opcode.sub, rhs);
                        try stack.push(value);
                        continue;
                    }
                }

                std.debug.panic("error: empty stack when doing subtraction\n", .{});
            },
            .Mul => |typeinfo| {
                const right = stack.pop();
                const left = stack.pop();

                if (left) |lhs| {
                    if (right) |rhs| {
                        const value = Opcode.perform_op(typeinfo, lhs, Opcode.mul, rhs);
                        try stack.push(value);
                        continue;
                    }
                }

                std.debug.panic("error: empty stack when doing multiplication\n", .{});
            },
            .Div => |typeinfo| {
                const right = stack.pop();
                const left = stack.pop();

                if (left) |lhs| {
                    if (right) |rhs| {
                        const value = Opcode.perform_op(typeinfo, lhs, Opcode.div, rhs);
                        try stack.push(value);
                        continue;
                    }
                }

                std.debug.panic("error: empty stack when doing division\n", .{});
            },
            .Return => |_| {
                const value = stack.pop();
                if (value) |v| {
                    std.process.exit(@intCast(v));
                    continue;
                }

                std.debug.panic("error: empty stack when returning\n", .{});
            },
            .Print => |typeinfo| {
                const value = stack.pop();

                if (value) |v| {
                    _ = Opcode.perform_op(typeinfo, v, Opcode.print, 0);
                    continue;
                }

                std.debug.panic("error: empty stack when printing\n", .{});
            },
            .Push => |value| {
                try stack.push(value);
            },
            .Set => |index| {
                const value = stack.pop();
                if (value) |v| {
                    const storage = @as([*]u128, @alignCast(@ptrCast(memory.*)));
                    storage[index] = v;
                }
            },
            .Get => |index| {
                const storage = @as([*]u128, @alignCast(@ptrCast(memory.*)));
                const value = storage[index];
                try stack.push(value);
            },
        }
    }
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();

    var args = try std.process.argsWithAllocator(allocator);
    defer args.deinit();
    _ = args.skip();

    var stack = try Dyn(u128).init(allocator);

    const maybe_filename = args.next();
    if (maybe_filename) |filename| {
        var file = try std.fs.cwd().openFile(filename, .{});
        defer file.close();

        var buf_reader = std.io.bufferedReader(file.reader());
        var in_stream = buf_reader.reader();

        var is_start = true;
        var buf: [1024]u8 = undefined;
        var memory: []u8 = undefined;

        while (try in_stream.readUntilDelimiterOrEof(&buf, '\n')) |line| {
            if (is_start) {
                if (std.mem.eql(u8, "PREALLOC ", line[0..9])) {
                    const num_line = if (line[line.len - 1] == '\r') line[9 .. line.len - 1] else line[9..];
                    const amount = try std.fmt.parseUnsigned(usize, num_line, 10);
                    memory = try allocator.alloc(u8, amount);
                }
                is_start = false;
                continue;
            }

            try interpret(line, &stack, &memory);
        }

        // std.debug.print("memory: {any}", .{memory});
    }
}
