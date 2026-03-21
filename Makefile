# Makefile for Mouse Disc
# Build distributable packages

VERSION := 1.0.0
PKG_NAME := mouse-disc-$(VERSION)
BUILD_DIR := build

.PHONY: all clean install uninstall user-install package appimage

all: package

package: $(BUILD_DIR)/$(PKG_NAME).tar.gz

$(BUILD_DIR)/$(PKG_NAME).tar.gz: $(BUILD_DIR)/$(PKG_NAME)
	@echo "Creating tarball..."
	cd $(BUILD_DIR) && tar czf $(PKG_NAME).tar.gz $(PKG_NAME)
	@echo "Package ready: $(BUILD_DIR)/$(PKG_NAME).tar.gz"

$(BUILD_DIR)/$(PKG_NAME): clean
	@echo "Building package structure..."
	mkdir -p $@/src
	mkdir -p $@/src/core
	mkdir -p $@/src/tabs
	mkdir -p $@/src/tabs/{ai,apps,controls,music,power}

	# Copy source files
	cp main.py $@/src/
	cp config.py $@/src/
	cp core/*.py $@/src/core/
	cp tabs/__init__.py $@/src/tabs/
	cp tabs/*.py $@/src/tabs/ 2>/dev/null || true
	cp tabs/ai/*.py $@/src/tabs/ai/
	cp tabs/apps/*.py $@/src/tabs/apps/
	cp tabs/controls/*.py $@/src/tabs/controls/
	cp tabs/music/*.py $@/src/tabs/music/
	cp tabs/power/*.py $@/src/tabs/power/

	# Copy launcher and metadata
	cp mouse-disc $@/
	cp mouse-disc.desktop $@/
	cp README.md $@/
	cp requirements.txt $@/
	cp LICENSE $@/ 2>/dev/null || echo "MIT License" > $@/LICENSE

	# Make launcher executable
	chmod +x $@/mouse-disc

	@echo "Done!"

install: $(BUILD_DIR)/$(PKG_NAME)
	@echo "Installing Mouse Disc system-wide..."

	# Install to /opt
	sudo mkdir -p /opt/mouse-disc
	sudo cp -r $(BUILD_DIR)/$(PKG_NAME)/* /opt/mouse-disc/
	sudo chmod +x /opt/mouse-disc/mouse-disc

	# Create symlink in /usr/local/bin
	sudo ln -sf /opt/mouse-disc/mouse-disc /usr/local/bin/mouse-disc

	# Install desktop entry
	sudo mkdir -p /usr/share/applications
	sudo cp mouse-disc.desktop /usr/share/applications/
	sudo sed -i 's|Exec=.*|Exec=/opt/mouse-disc/mouse-disc|' /usr/share/applications/mouse-disc.desktop

	# Update desktop database
	sudo update-desktop-database /usr/share/applications 2>/dev/null || true

	@echo "Mouse Disc installed to /opt/mouse-disc"
	@echo "Run with: mouse-disc"

user-install: $(BUILD_DIR)/$(PKG_NAME)
	@echo "Installing Mouse Disc for current user..."

	# Extract to home
	tar xzf $(BUILD_DIR)/$(PKG_NAME).tar.gz -C ~

	# Create symlink
	mkdir -p ~/.local/bin
	ln -sf ~/$(PKG_NAME)/mouse-disc ~/.local/bin/

	# Copy desktop entry
	mkdir -p ~/.local/share/applications ~/.config/autostart
	sed 's|Exec=.*|Exec='"$$HOME"'/.local/bin/mouse-disc|' mouse-disc.desktop > ~/.local/share/applications/mouse-disc.desktop
	cp ~/.local/share/applications/mouse-disc.desktop ~/.config/autostart/

	# Update desktop database
	update-desktop-database ~/.local/share/applications 2>/dev/null || true

	@echo "Mouse Disc installed to ~/$(PKG_NAME)"
	@echo "Run with: mouse-disc"
	@echo "Auto-start enabled"

uninstall:
	@echo "Uninstalling Mouse Disc..."
	sudo rm -rf /opt/mouse-disc
	sudo rm -f /usr/local/bin/mouse-disc
	sudo rm -f /usr/share/applications/mouse-disc.desktop
	sudo update-desktop-database /usr/share/applications 2>/dev/null || true
	@echo "Uninstalled!"

clean:
	rm -rf $(BUILD_DIR)

appimage:
	@echo "AppImage build requires appimagetool"
	@echo "Not yet implemented - use 'make package' for now"
