"""Import this library to allow the program to be used as an independent script."""
from plover import system

if not hasattr(system, "KEYS"):
	from plover.registry import registry
	registry.update()
	system.setup("English Stenotype")
