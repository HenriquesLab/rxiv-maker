class RxivMaker < Formula
  desc "Automated LaTeX article generation with modern CLI and figure support"
  homepage "https://github.com/henriqueslab/rxiv-maker"
  license "MIT"

  # Determine the appropriate binary based on architecture
  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/henriqueslab/rxiv-maker/releases/download/v1.4.8/rxiv-maker-macos-arm64.tar.gz"
      sha256 "placeholder"
    else
      url "https://github.com/henriqueslab/rxiv-maker/releases/download/v1.4.8/rxiv-maker-macos-x64-intel.tar.gz"
      sha256 "placeholder"
    end
  end

  on_linux do
    if Hardware::CPU.intel?
      url "https://github.com/henriqueslab/rxiv-maker/releases/download/v1.4.8/rxiv-maker-linux-x64.tar.gz"
      sha256 "placeholder"
    else
      odie "Linux ARM64 is not currently supported. Please use 'pip install rxiv-maker' instead."
    end
  end

  def install
    # Install the pre-compiled binary
    bin.install "rxiv"

    # Make sure the binary is executable
    chmod 0755, bin/"rxiv"
  end

  def caveats
    <<~EOS
      🚀 rxiv-maker has been installed as a pre-compiled binary!

      ⚡ This is much faster than the previous Python-based installation
      ✅ No Python dependencies required - it's completely self-contained

      For full functionality, you'll still need LaTeX:

      macOS:
        brew install --cask mactex     # Full LaTeX distribution (recommended)
        # OR
        brew install --cask basictex   # Minimal LaTeX installation

      Linux:
        # Ubuntu/Debian:
        sudo apt-get install texlive-latex-base texlive-latex-extra
        # Fedora/RHEL:
        sudo dnf install texlive-latex texlive-latex-extra

      🚀 Quick start:
        rxiv init my-paper    # Initialize a new manuscript
        cd my-paper
        rxiv pdf              # Generate PDF
        rxiv --help           # Show help

      📖 Documentation: https://github.com/henriqueslab/rxiv-maker#readme

      💡 Note: This binary distribution includes all Python dependencies.
          If you need the Python package for development, use: pip install rxiv-maker
    EOS
  end

  test do
    # Test that the CLI is working
    assert_match "rxiv-maker", shell_output("#{bin}/rxiv --version")

    # Test basic functionality
    system bin/"rxiv", "--help"

    # Test initialization in a temporary directory
    testpath = "test_manuscript"
    system bin/"rxiv", "init", testpath, "--no-interactive"
    assert_predicate testpath/"00_CONFIG.yml", :exist?
    assert_predicate testpath/"01_MAIN.md", :exist?
    assert_predicate testpath/"03_REFERENCES.bib", :exist?
  end
end
