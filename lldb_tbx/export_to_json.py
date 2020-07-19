"""Serialize and export an object as JSON."""

from pathlib import Path
import argparse
import collections
import json
import logging
import shlex

import lldb


class TreeNode(dict):
    """Container for storing data from `lldb.SBValue`s."""

    def __init__(self):
        super().__init__()
        self.__dict__ = self

    def add_child(self, name: str, child_node):
        self.__dict__[name] = child_node

    def set_metadata(self, lldb_obj: lldb.SBValue):
        self.__dict__["@type_name"] = lldb_obj.GetTypeName()
        self.__dict__["@location"] = lldb_obj.GetLocation()
        if lldb_obj.GetNumChildren() == 0:
            self.__dict__["@value"] = lldb_obj.GetValue()
            self.__dict__["@value_unsigned"] = lldb_obj.GetValueAsUnsigned()
            self.__dict__["@value_signed"] = lldb_obj.GetValueAsSigned()


def get_name_or_address(lldb_obj: lldb.SBValue) -> str:
    return (
        "<anonymous at {}>".format(lldb_obj.GetAddress())
        if lldb_obj.GetName() is None
        else lldb_obj.GetName()
    )


def convert_to_dict(root_obj: lldb.SBValue) -> TreeNode:
    root_node = TreeNode()
    root_node.set_metadata(root_obj)
    queue = collections.deque([(root_obj, root_node)])
    while queue:
        parent_obj, parent_node = queue.popleft()
        for child_obj in parent_obj:
            child_node = TreeNode()
            child_node.set_metadata(child_obj)

            queue.append((child_obj, child_node))

            child_name = get_name_or_address(child_obj)
            # Assert that the child name does not clash with our metadata keys
            assert not child_name.startswith(
                "@"
            ), "Potential clash with metadata keys. Please open an issue"
            parent_node.add_child(child_name, child_node)

    return root_node


class ExportToJson:
    """Class that will be registered as `lldb` command `export_to_json`."""

    def __init__(self, _debugger: lldb.SBDebugger, _session_dict):
        self._logger = logging.getLogger("export_to_json")
        self._parser = argparse.ArgumentParser(
            prog="export_to_json", description="Serialize and export an object to JSON"
        )
        self._parser.add_argument(
            "variable", type=str, help="Name of the variable to be exported"
        )
        self._parser.add_argument(
            "output_filename",
            type=str,
            nargs="?",
            help="Output filename (default: same as variable)",
        )
        thread_spec = self._parser.add_mutually_exclusive_group(required=False)
        thread_spec.add_argument(
            "--thread_index",
            type=int,
            required=False,
            default=None,
            help="Specify thread by index (default: currently selected thread)",
        )
        thread_spec.add_argument(
            "--thread_id",
            type=int,
            required=False,
            default=None,
            help="Specify thread by id (default: currently selected thread)",
        )
        self._parser.add_argument(
            "--frame_index",
            type=int,
            required=False,
            default=None,
            help="Specify frame by index (default: currently selected frame)",
        )
        self._parser.add_argument(
            "--indent",
            type=int,
            required=False,
            default=None,
            help="Indent for JSON (default: no indenting)",
        )

    def __call__(
        self,
        debugger: lldb.SBDebugger,
        command: str,
        exe_ctx: lldb.SBExecutionContext,
        result: lldb.SBCommandReturnObject,
    ):
        logging.basicConfig(level=logging.INFO)
        args = self._parser.parse_args(shlex.split(command))
        process = exe_ctx.GetProcess()
        if not process.IsValid():
            self._logger.error("Process '%s' is not valid. Aborting.", process)
            return
        self._logger.info("Using %s", process)

        if args.thread_id is not None:
            thread = process.GetThreadByID(args.thread_id)
        elif args.thread_index is not None:
            thread = process.GetThreadByIndexID(args.thread_index)
        else:
            thread = exe_ctx.GetThread()
        if not thread.IsValid():
            self._logger.error("Thread '%s' is not valid. Aborting.", thread)
            return
        self._logger.info("Using %s", thread)

        if args.frame_index is not None:
            frame = thread.GetFrameAtIndex(args.frame_index)
        else:
            frame = exe_ctx.GetFrame()
        if not frame.IsValid():
            self._logger.error("Frame '%s' is not valid. Aborting.", frame)
            return
        self._logger.info("Using %s", frame)

        lldb_obj = frame.FindVariable(args.variable)
        if not lldb_obj.IsValid():
            self._logger.error("Value '%s' is not valid. Aborting.", lldb_obj)
            return
        self._logger.info("Using %s", lldb_obj)

        var_as_dict = {get_name_or_address(lldb_obj): convert_to_dict(lldb_obj)}

        output_path = Path(
            "{}.json".format(args.variable)
            if args.output_filename is None
            else args.output_filename
        ).resolve()
        self._logger.info("Writing to file '%s'", output_path)
        with open(output_path, "w") as f_handle:
            json.dump(var_as_dict, f_handle, indent=args.indent)

    def get_short_help(self):
        print(self._parser.description)

    def get_long_help(self):
        self._parser.print_help()
