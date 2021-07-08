from binaryninja import *
import re

def load_dolphin_map(bv):
	map_filename = get_open_filename_input("Select map file")
	if map_filename == "":
		return
	with open(map_filename, "r") as map_file:
		print("Loading symbol file")
		in_section_layouts = False
		for line in map_file:
			# Find section layout section of the file, there should only be the memory map after this
			if " section layout" in line:
				in_section_layouts = True
			elif "Memory map:" in line:
				in_section_layouts = False

			if not in_section_layouts:
				continue

			in_section_layouts = True

			if len(line) <= 30:
				#print("Removing line for length <= 30")
				continue
			tokens = re.split("[ \t]", line.rstrip().lstrip())
			if len(tokens) < 5:
				#print("Removing line for tokens < 5 ({})".format(len(tokens)))
				continue

			if "UNUSED" in tokens and "........" in tokens:
				#print("Removing line for unused symbol")
				continue

			while "" in tokens:
				tokens.remove("")


			address = int(tokens[2], 16)
			name = tokens[4]

			# Skip anonymous symbols and subsection symbols
			if name.startswith("@") or name.startswith(".") or name.startswith("(entry"):
				continue

			# Determine kind of symbol
			segment = bv.get_segment_at(address)
			if not segment:
				#name = "EXT_{}_{:08x}".format(name, address)
				symbol_type = SymbolType.ExternalSymbol
			elif segment.executable:
				symbol_type = SymbolType.FunctionSymbol
			else:
				symbol_type = SymbolType.DataSymbol
			
			existing_symbol = bv.get_symbol_at(address)
			# HACK: There's a bug in Binja that means user symbols won't
			# properly ovewrite unless the auto symbol is undefined first.
			if existing_symbol and existing_symbol.auto:
				bv.undefine_auto_symbol(existing_symbol)
				existing_symbol = None

			if not existing_symbol or existing_symbol.auto:
				print("DolphinMap: {:08x}: {}".format(address, name))
				bv.define_user_symbol(Symbol(
					symbol_type,
					address,
					name,
					namespace = " ".join(tokens[5:])
				))
			else:
				print("DolphinMap: Already named, skipping {:08x}: {}".format(address, name))

			if symbol_type == SymbolType.FunctionSymbol and bv.get_function_at(address) == None:
				bv.create_user_function(address, Architecture["ppc"].standalone_platform)
			elif symbol_type == SymbolType.DataSymbol and bv.get_data_var_at(address) == None:
				bv.define_user_data_var(address, bv.parse_type_string("void")[0])

binaryninja.PluginCommand.register(
	"Dolphin\\Load Dolphin map",
	"Loads a Dolphin .map file",
	load_dolphin_map
)