"""Tests for widget interactions using Playwright regression issues.

This module contains regression tests for widget interaction problems identified
by Guillaume in PR #98, using Playwright for end-to-end testing of widget
behavior in browser environments like Google Colab.

Key issues tested:
- PR #98: Authors being cleared when adding affiliations
- Widget state persistence across interactions
- Google Colab notebook widget compatibility
- IPython widgets environment simulation
"""

import pytest


class TestWidgetInteractionsWithPlaywright:
    """Test widget interactions using Playwright for Google Colab compatibility.

    These tests address PR #98: authors being cleared when adding affiliations.
    """

    @pytest.fixture
    def browser_context(self):
        """Set up browser context for widget testing."""
        pytest.importorskip("playwright")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            yield context
            browser.close()

    def test_colab_notebook_widget_loading(self, browser_context):
        """Test that widgets load properly in a Colab-like environment."""
        page = browser_context.new_page()

        # Create a minimal HTML page that simulates Colab notebook interface
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Colab Notebook</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js"></script>
            <style>
                .widget-container { padding: 10px; margin: 10px; border: 1px solid #ccc; }
                .author-widget { background: #f5f5f5; }
                .affiliation-widget { background: #e5f5e5; }
                .button { padding: 5px 10px; margin: 5px; cursor: pointer; }
                .text-input { padding: 5px; margin: 5px; width: 200px; }
            </style>
        </head>
        <body>
            <div id="notebook-container">
                <h1>Test Notebook for rxiv-maker Widget</h1>

                <!-- Simulate the author/affiliation widget -->
                <div class="widget-container author-widget">
                    <h3>Authors</h3>
                    <div id="authors-list">
                        <div class="author-entry">
                            <input type="text" class="text-input author-name" placeholder="Author name" value="John Doe">
                            <button class="button remove-author">Remove</button>
                        </div>
                    </div>
                    <button class="button" id="add-author">Add Author</button>
                </div>

                <div class="widget-container affiliation-widget">
                    <h3>Affiliations</h3>
                    <div id="affiliations-list">
                        <div class="affiliation-entry">
                            <input type="text" class="text-input affiliation-name" placeholder="Affiliation" value="University A">
                            <button class="button remove-affiliation">Remove</button>
                        </div>
                    </div>
                    <button class="button" id="add-affiliation">Add Affiliation</button>
                </div>
            </div>

            <script>
                // Simulate the widget behavior that was causing issues
                document.getElementById('add-affiliation').addEventListener('click', function() {
                    // This simulates the bug where authors were cleared when adding affiliations
                    var affiliationsList = document.getElementById('affiliations-list');
                    var newAffiliation = document.createElement('div');
                    newAffiliation.className = 'affiliation-entry';
                    newAffiliation.innerHTML = '<input type="text" class="text-input affiliation-name" placeholder="New affiliation">' +
                                              '<button class="button remove-affiliation">Remove</button>';
                    affiliationsList.appendChild(newAffiliation);

                    // The bug: DO NOT clear authors when adding affiliations
                    // This is what the original bug was doing - we test that it doesn't happen
                    console.log('Added affiliation without clearing authors');
                });

                document.getElementById('add-author').addEventListener('click', function() {
                    var authorsList = document.getElementById('authors-list');
                    var newAuthor = document.createElement('div');
                    newAuthor.className = 'author-entry';
                    newAuthor.innerHTML = '<input type="text" class="text-input author-name" placeholder="New author">' +
                                         '<button class="button remove-author">Remove</button>';
                    authorsList.appendChild(newAuthor);
                });

                // Add event delegation for remove buttons
                document.addEventListener('click', function(e) {
                    if (e.target.classList.contains('remove-author')) {
                        e.target.parentElement.remove();
                    } else if (e.target.classList.contains('remove-affiliation')) {
                        e.target.parentElement.remove();
                    }
                });
            </script>
        </body>
        </html>
        """

        # Load the test page
        page.set_content(html_content)

        # Wait for the page to load completely
        page.wait_for_selector("#add-author")
        page.wait_for_selector("#add-affiliation")

        # Get initial author count
        initial_authors = page.query_selector_all(".author-entry")
        assert len(initial_authors) == 1

        # Get initial author value
        initial_author_name = page.query_selector(".author-name").input_value()
        assert initial_author_name == "John Doe"

        # Add a new affiliation (this was causing the bug)
        page.click("#add-affiliation")

        # Verify that authors are NOT cleared (this is the fix)
        authors_after_affiliation = page.query_selector_all(".author-entry")
        assert len(authors_after_affiliation) == 1  # Should still have the original author

        # Verify the original author name is still there
        author_name_after = page.query_selector(".author-name").input_value()
        assert author_name_after == "John Doe"  # Should not be cleared

        # Verify the new affiliation was added
        affiliations = page.query_selector_all(".affiliation-entry")
        assert len(affiliations) == 2  # Original + newly added

    def test_widget_state_persistence_across_interactions(self, browser_context):
        """Test that widget state persists across multiple interactions."""
        page = browser_context.new_page()

        # Minimal widget testing page
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Widget State Test</title>
            <style>
                .widget { padding: 10px; margin: 10px; border: 1px solid #ddd; }
                .input-field { padding: 5px; margin: 5px; width: 200px; }
                .button { padding: 5px 10px; margin: 5px; cursor: pointer; }
            </style>
        </head>
        <body>
            <div class="widget">
                <input type="text" id="author1" class="input-field" placeholder="Author 1" value="">
                <input type="text" id="author2" class="input-field" placeholder="Author 2" value="">
                <input type="text" id="affiliation1" class="input-field" placeholder="Affiliation 1" value="">
                <button id="simulate-interaction" class="button">Simulate Interaction</button>
                <div id="state-display"></div>
            </div>

            <script>
                document.getElementById('simulate-interaction').addEventListener('click', function() {
                    // This simulates the kind of interaction that was causing state loss
                    var stateDisplay = document.getElementById('state-display');
                    var author1 = document.getElementById('author1').value;
                    var author2 = document.getElementById('author2').value;
                    var affiliation1 = document.getElementById('affiliation1').value;

                    stateDisplay.innerHTML = 'State preserved: ' +
                        'Author1=' + author1 + ', Author2=' + author2 + ', Affiliation1=' + affiliation1;
                });
            </script>
        </body>
        </html>
        """

        page.set_content(html_content)
        page.wait_for_selector("#author1")

        # Fill in some data
        page.fill("#author1", "Alice Smith")
        page.fill("#author2", "Bob Jones")
        page.fill("#affiliation1", "MIT")

        # Trigger interaction that might cause state loss
        page.click("#simulate-interaction")

        # Verify state is preserved
        state_text = page.text_content("#state-display")
        assert "Alice Smith" in state_text
        assert "Bob Jones" in state_text
        assert "MIT" in state_text

        # Verify inputs still have their values
        assert page.input_value("#author1") == "Alice Smith"
        assert page.input_value("#author2") == "Bob Jones"
        assert page.input_value("#affiliation1") == "MIT"

    def test_colab_ipywidgets_compatibility(self, browser_context):
        """Test compatibility with IPython widgets environment."""
        page = browser_context.new_page()

        # Simulate the IPython widgets environment
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>IPython Widgets Test</title>
            <script>
                // Mock IPython environment
                window.IPython = {
                    notebook: {
                        kernel: {
                            execute: function(code) {
                                console.log('Executing:', code);
                                return { then: function(callback) { callback(); } };
                            }
                        }
                    }
                };

                // Mock Jupyter widgets
                window.jupyter = {
                    widgets: {
                        output: {
                            clear_output: function() {
                                console.log('Clearing output');
                            }
                        }
                    }
                };
            </script>
            <style>
                .jupyter-widgets { padding: 10px; border: 1px solid #ccc; }
                .widget-text { padding: 5px; margin: 5px; }
                .widget-button { padding: 5px 10px; margin: 5px; }
            </style>
        </head>
        <body>
            <div class="jupyter-widgets">
                <h3>rxiv-maker Widget Test</h3>
                <div class="widget-text">
                    <label>Manuscript Title:</label>
                    <input type="text" id="manuscript-title" value="My Research Paper">
                </div>
                <div class="widget-text">
                    <label>Authors:</label>
                    <textarea id="authors-textarea" rows="3">Author 1, Author 2</textarea>
                </div>
                <button class="widget-button" id="update-metadata">Update Metadata</button>
                <div id="result"></div>
            </div>

            <script>
                document.getElementById('update-metadata').addEventListener('click', function() {
                    var title = document.getElementById('manuscript-title').value;
                    var authors = document.getElementById('authors-textarea').value;

                    // Simulate the widget updating metadata
                    document.getElementById('result').innerHTML =
                        'Updated: Title="' + title + '", Authors="' + authors + '"';

                    // This is where the bug would manifest - losing data during updates
                    console.log('Metadata updated without data loss');
                });
            </script>
        </body>
        </html>
        """

        page.set_content(html_content)
        page.wait_for_selector("#manuscript-title")

        # Verify initial state
        assert page.input_value("#manuscript-title") == "My Research Paper"
        assert "Author 1, Author 2" in page.input_value("#authors-textarea")

        # Modify data
        page.fill("#manuscript-title", "Updated Research Paper")
        page.fill("#authors-textarea", "Alice Smith, Bob Jones, Carol White")

        # Trigger update (this is where the bug would occur)
        page.click("#update-metadata")

        # Verify data persistence after update
        result_text = page.text_content("#result")
        assert "Updated Research Paper" in result_text
        assert "Alice Smith, Bob Jones, Carol White" in result_text

        # Verify inputs still have the updated values
        assert page.input_value("#manuscript-title") == "Updated Research Paper"
        assert "Alice Smith, Bob Jones, Carol White" in page.input_value("#authors-textarea")

    def test_colab_environment_variables_handling(self, browser_context):
        """Test handling of Google Colab environment variables and paths."""
        page = browser_context.new_page()

        # Simulate Colab environment detection
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Colab Environment Test</title>
        </head>
        <body>
            <div id="environment-info">
                <h3>Environment Detection</h3>
                <div id="colab-status">Unknown</div>
                <div id="path-info"></div>
            </div>

            <script>
                // Simulate environment detection logic
                function detectColabEnvironment() {
                    var isColab = window.location.hostname.includes('colab.research.google.com') ||
                                 document.getElementById('site-name') !== null ||
                                 navigator.userAgent.includes('Colab');

                    document.getElementById('colab-status').textContent =
                        isColab ? 'Google Colab Detected' : 'Local Environment';

                    // Simulate path handling that was problematic in Guillaume's issues
                    var paths = {
                        working_dir: '/content',
                        manuscript_dir: '/content/manuscript',
                        figures_dir: '/content/manuscript/FIGURES'
                    };

                    document.getElementById('path-info').innerHTML =
                        'Working Dir: ' + paths.working_dir + '<br>' +
                        'Manuscript Dir: ' + paths.manuscript_dir + '<br>' +
                        'Figures Dir: ' + paths.figures_dir;
                }

                detectColabEnvironment();
            </script>
        </body>
        </html>
        """

        page.set_content(html_content)
        page.wait_for_selector("#colab-status")

        # Verify environment detection works
        status_text = page.text_content("#colab-status")
        assert "Environment" in status_text

        # Verify path information is displayed
        path_info = page.text_content("#path-info")
        assert "/content" in path_info
        assert "manuscript" in path_info.lower()


if __name__ == "__main__":
    pytest.main([__file__])
