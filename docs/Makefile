# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    = -anTW
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = temBoardagentAPI
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: serve
serve:
	cd $(BUILDDIR)/html; python3 -m http.server

.PHONY: watch
# Install python-watchdog or pip install watchdog
watch:
	clear;	watchmedo shell-command --drop --patterns="*.rst;conf.py" --recursive --command="clear; $(MAKE) html" $(SOURCEDIR)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
