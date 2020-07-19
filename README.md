# My `lldb` toolbox

> When you have learned to snatch the error code from the trap frame, it will be time for you to leave.

[_The Tao of Programming_ by Geoffrey James](https://www.mit.edu/~xela/tao.html)

![Lints and checks](https://github.com/mp4096/lldb-tbx/workflows/Lints%20and%20checks/badge.svg)

This is a collection of useful actions for `lldb`, implemented as embedded Python scripts.
Tested with `lldb-10` and Python 3.6+.
No third-party dependencies required except for `lldb`'s Python module itself.

## Installation

Clone this repo into `$REPO_LOCATION` and add the following lines to your `~/.lldbinit`:

```
command script import $REPO_LOCATION/lldb-tbx/lldb_tbx

command script add -c lldb_tbx.ExportToJson export_to_json
```

You can leave out the commands you don't need.

## Commands

Currently available commands:

* [`export_to_json`](#export_to_json) : serialize an object and export it as JSON

### `export_to_json`

For usage, type `export_to_json --help`.

Sample code:

```cpp
#import <array>
#import <cstdint>

template <typename T> struct Bar {
  std::array<T, 2U> a{};
  std::int8_t i{};
};

int main() {
  Bar<float> bar{
      {0.1F, -0.1F},
      -5,
  };
  // break here
}
```

```
$ clang++-10 -std=c++17 -g -O0 -fstandalone-debug -Wall main.cpp
$ lldb-10 a.out
(lldb) break set -f main.cpp -l 16
(lldb) r
(lldb) export_to_json bar --indent 4
```

Result:

```json
{
    "bar": {
        "@type_name": "Bar<float>",
        "@location": "0x00007fffffffdca0",
        "a": {
            "@type_name": "std::array<float, 2>",
            "@location": "0x00007fffffffdca0",
            "_M_elems": {
                "@type_name": "std::__array_traits<float, 2>::_Type",
                "@location": "0x00007fffffffdca0",
                "[0]": {
                    "@type_name": "float",
                    "@location": "0x00007fffffffdca0",
                    "@value": "0.100000001",
                    "@value_unsigned": 0,
                    "@value_signed": 0
                },
                "[1]": {
                    "@type_name": "float",
                    "@location": "0x00007fffffffdca4",
                    "@value": "-0.100000001",
                    "@value_unsigned": 0,
                    "@value_signed": 0
                }
            }
        },
        "i": {
            "@type_name": "int8_t",
            "@location": "0x00007fffffffdca8",
            "@value": "'\\xfb'",
            "@value_unsigned": 4294967291,
            "@value_signed": -5
        }
    }
}
```
