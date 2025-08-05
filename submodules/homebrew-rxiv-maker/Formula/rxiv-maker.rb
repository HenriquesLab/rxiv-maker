class RxivMaker < Formula
  desc "Automated LaTeX article generation with modern CLI and figure support"
  homepage "https://github.com/HenriquesLab/rxiv-maker"
  url "https://files.pythonhosted.org/packages/source/r/rxiv-maker/rxiv_maker-1.4.15.tar.gz"
  sha256 "PLACEHOLDER_SHA256_WILL_BE_UPDATED_ON_RELEASE"
  license "MIT"

  depends_on "uv"
  depends_on "texlive"

  def install
    # Create virtual environment using uv for fast isolation
    system "uv", "venv", libexec
    
    # Install rxiv-maker and all dependencies using uv
    system "uv", "pip", "install", "--python", libexec/"bin/python", "rxiv-maker==#{version}"
    
    # Create executable wrapper in bin
    (bin/"rxiv").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" -m rxiv_maker.cli "$@"
    EOS
    chmod 0755, bin/"rxiv"
  end

  def caveats
    <<~EOS
      🚀 rxiv-maker has been installed successfully!

      📦 This installation includes all Python dependencies and LaTeX (TeXLive) in isolated environments.
      ✅ You're ready to generate PDFs immediately - no additional setup required!

      🚀 Quick start:
        rxiv init my-paper    # Initialize a new manuscript
        cd my-paper
        rxiv pdf              # Generate PDF (LaTeX included!)
        rxiv --help           # Show help

      🎨 Optional enhancements (install separately if needed):
        brew install node     # For Mermaid diagrams
        brew install r        # For R-based figures

      📖 Documentation: https://github.com/HenriquesLab/rxiv-maker#readme

      💡 Note: This Homebrew installation uses uv for fast Python package isolation.
          LaTeX (TeXLive) is automatically included for immediate PDF generation.
    EOS
  end

  test do
    # Test that the CLI is working
    assert_match "rxiv-maker", shell_output("#{bin}/rxiv --version")

    # Test basic functionality
    system bin/"rxiv", "--help"

    # Test that LaTeX is available and working
    system "which", "pdflatex"
    assert_match "TeX Live", shell_output("pdflatex --version")

    # Test initialization in a temporary directory
    testpath = "test_manuscript"
    system bin/"rxiv", "init", testpath, "--no-interactive"
    assert_predicate testpath/"00_CONFIG.yml", :exist?
    assert_predicate testpath/"01_MAIN.md", :exist?
    assert_predicate testpath/"03_REFERENCES.bib", :exist?

    # Test PDF generation capability (validation only - no actual PDF build in tests)
    system bin/"rxiv", "validate", testpath, "--no-doi"

    # Test that check-installation reports LaTeX as available
    output = shell_output("#{bin}/rxiv check-installation 2>&1")
    assert_match "LaTeX", output
  end
end
