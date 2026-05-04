# vidget.mk — include this in any project's Makefile to get vidget targets
#
# Setup in your project:
#   VIDGET_DIR := /path/to/jre-vidget   (or use a git submodule)
#   include $(VIDGET_DIR)/bin/vidget.mk
#
# Then:
#   make vidget-setup                          # build the image once
#   make vidget-download URL="https://..."     # download a video
#   make vidget-batch    FILE=urls.txt         # batch download
#   make vidget-formats  URL="https://..."     # list formats

VIDGET_DIR    ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))..
VIDGET_IMAGE  ?= jre-vidget
VIDGET_OUTPUT ?= $(PWD)/downloads

.PHONY: vidget-setup vidget-update vidget-download vidget-batch vidget-formats

vidget-setup:
	docker build -t $(VIDGET_IMAGE) $(VIDGET_DIR)
	@echo "✓  $(VIDGET_IMAGE) ready — run: make vidget-download URL=\"https://...\""

vidget-update:
	docker build --no-cache -t $(VIDGET_IMAGE) $(VIDGET_DIR)

vidget-download:
	@test -n "$(URL)" || (echo "Usage: make vidget-download URL=\"https://...\"" && exit 1)
	@mkdir -p "$(VIDGET_OUTPUT)"
	docker run --rm \
		-v "$(VIDGET_OUTPUT):/downloads" \
		$(VIDGET_IMAGE) download "$(URL)" --output /downloads

vidget-batch:
	@test -n "$(FILE)" || (echo "Usage: make vidget-batch FILE=urls.txt" && exit 1)
	@mkdir -p "$(VIDGET_OUTPUT)"
	docker run --rm \
		-v "$(VIDGET_OUTPUT):/downloads" \
		-v "$(abspath $(FILE)):/urls.txt:ro" \
		$(VIDGET_IMAGE) batch /urls.txt --output /downloads

vidget-formats:
	@test -n "$(URL)" || (echo "Usage: make vidget-formats URL=\"https://...\"" && exit 1)
	docker run --rm $(VIDGET_IMAGE) formats "$(URL)"
