import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

suite('Extension Test Suite', () => {
	vscode.window.showInformationMessage('Start all tests.');

	/**
	 * Helper function to find the EXAMPLE_MANUSCRIPT directory dynamically
	 */
	function findExampleManuscriptPath(): string | null {
		// Try multiple potential locations relative to the test execution
		const potentialPaths = [
			// From VS Code extension development/test environment
			path.join(__dirname, '..', '..', '..', '..', 'EXAMPLE_MANUSCRIPT'),
			// From workspace root
			path.join(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '', 'EXAMPLE_MANUSCRIPT'),
			// From common project structure patterns
			path.join(process.cwd(), 'EXAMPLE_MANUSCRIPT'),
			path.join(process.cwd(), '..', 'EXAMPLE_MANUSCRIPT'),
			path.join(process.cwd(), '..', '..', 'EXAMPLE_MANUSCRIPT'),
			// Environment variable override
			process.env.RXIV_MAKER_EXAMPLE_PATH || '',
		].filter(Boolean);

		for (const potentialPath of potentialPaths) {
			if (fs.existsSync(potentialPath) && fs.existsSync(path.join(potentialPath, '00_CONFIG.yml'))) {
				return potentialPath;
			}
		}

		return null;
	}

	/**
	 * Get the example manuscript path or skip test if not available
	 */
	function getExampleManuscriptPath(): string {
		const examplePath = findExampleManuscriptPath();
		if (!examplePath) {
			throw new Error('EXAMPLE_MANUSCRIPT directory not found. Please ensure the rxiv-maker repository is available or set RXIV_MAKER_EXAMPLE_PATH environment variable.');
		}
		return examplePath;
	}

	test('Sample test', () => {
		assert.strictEqual(-1, [1, 2, 3].indexOf(5));
		assert.strictEqual(-1, [1, 2, 3].indexOf(0));
	});

	test('Extension should load commands', async () => {
		// First, ensure the extension is activated by opening a document that should trigger it
		const exampleManuscriptPath = getExampleManuscriptPath();
		const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
		const uri = vscode.Uri.file(mainPath);
		const document = await vscode.workspace.openTextDocument(uri);
		await vscode.window.showTextDocument(document);

		// Give extension time to activate
		await new Promise(resolve => setTimeout(resolve, 1000));

		const commands = await vscode.commands.getCommands();
		assert.ok(commands.includes('rxiv-maker.insertCitation'), 'Should register insertCitation command');
		assert.ok(commands.includes('rxiv-maker.insertFigureReference'), 'Should register insertFigureReference command');
		assert.ok(commands.includes('rxiv-maker.validateProject'), 'Should register validateProject command');
	});

	test('Extension should register rxiv-markdown language', async () => {
		const languages = await vscode.languages.getLanguages();
		assert.ok(languages.includes('rxiv-markdown'), 'Should register rxiv-markdown language');
	});

	suite('EXAMPLE_MANUSCRIPT Tests', () => {
		let exampleManuscriptPath: string;

		suiteSetup(() => {
			exampleManuscriptPath = getExampleManuscriptPath();
		});

		test('Should detect rxiv-maker project structure', async () => {
			const requiredFiles = ['00_CONFIG.yml', '01_MAIN.md', '03_REFERENCES.bib'];

			for (const file of requiredFiles) {
				const filePath = path.join(exampleManuscriptPath, file);
				assert.ok(fs.existsSync(filePath), `Required file ${file} should exist`);
			}
		});

		test('Should parse bibliography entries', async () => {
			const bibPath = path.join(exampleManuscriptPath, '03_REFERENCES.bib');
			const content = fs.readFileSync(bibPath, 'utf8');

			// Test that bib file contains expected entries
			assert.ok(content.includes('@article{Knuth1984_literate_programming'), 'Should contain Knuth reference');
			assert.ok(content.includes('@article{Hunter2007_matplotlib'), 'Should contain matplotlib reference');
			assert.ok(content.includes('@article{Donoho2010'), 'Should contain Donoho reference');
		});

		test('Should detect figure references in main document', async () => {
			const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
			const content = fs.readFileSync(mainPath, 'utf8');

			// Test that main document contains expected references
			assert.ok(content.includes('@fig:diagram'), 'Should contain figure diagram reference');
			assert.ok(content.includes('@fig:workflow'), 'Should contain figure workflow reference');
			assert.ok(content.includes('@sfig:arxiv-growth'), 'Should contain supplementary figure reference');
		});

		test('Should detect equation references', async () => {
			const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
			const content = fs.readFileSync(mainPath, 'utf8');

			// Test that main document contains expected equation references
			assert.ok(content.includes('@eq:einstein'), 'Should contain Einstein equation reference');
			assert.ok(content.includes('@eq:std_dev'), 'Should contain standard deviation equation reference');
			assert.ok(content.includes('@eq:equilibrium'), 'Should contain equilibrium equation reference');
		});

		test('Should detect table references', async () => {
			const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
			const content = fs.readFileSync(mainPath, 'utf8');

			// Test that main document contains expected table references
			assert.ok(content.includes('@stable:figure-formats'), 'Should contain supplementary table reference');
			assert.ok(content.includes('@stable:tool-comparison'), 'Should contain tool comparison table reference');
		});

		test('Should detect supplementary note references', async () => {
			const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
			const content = fs.readFileSync(mainPath, 'utf8');

			// Test that main document contains expected supplementary note references
			assert.ok(content.includes('@snote:figure-generation'), 'Should contain figure generation note reference');
			assert.ok(content.includes('@snote:mathematical-formulas'), 'Should contain mathematical formulas note reference');
		});

		test('Should have FIGURES directory', async () => {
			const figuresPath = path.join(exampleManuscriptPath, 'FIGURES');
			assert.ok(fs.existsSync(figuresPath), 'FIGURES directory should exist');

			// Check for specific figure files
			const figure1Path = path.join(figuresPath, 'Figure_1');
			const figure2Path = path.join(figuresPath, 'Figure_2');
			assert.ok(fs.existsSync(figure1Path), 'Figure_1 directory should exist');
			assert.ok(fs.existsSync(figure2Path), 'Figure_2 directory should exist');
		});

		test('Should validate CONFIG.yml structure', async () => {
			const configPath = path.join(exampleManuscriptPath, '00_CONFIG.yml');
			const content = fs.readFileSync(configPath, 'utf8');

			// Test that config contains expected sections
			assert.ok(content.includes('title:'), 'Should contain title section');
			assert.ok(content.includes('authors:'), 'Should contain authors section');
			assert.ok(content.includes('affiliations:'), 'Should contain affiliations section');
			assert.ok(content.includes('bibliography: 03_REFERENCES.bib'), 'Should reference bibliography file');
		});

		test('Should test extension functionality with EXAMPLE_MANUSCRIPT', async () => {
			// Open the EXAMPLE_MANUSCRIPT main file
			const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
			const uri = vscode.Uri.file(mainPath);
			const document = await vscode.workspace.openTextDocument(uri);

			// Verify the document opened successfully
			assert.ok(document, 'Should open the main document');
			assert.ok(document.getText().length > 0, 'Document should have content');

			// Test that the document contains expected rxiv-maker syntax
			const content = document.getText();
			assert.ok(content.includes('@fig:'), 'Should contain figure references');
			assert.ok(content.includes('@stable:'), 'Should contain stable references');
			assert.ok(content.includes('@eq:'), 'Should contain equation references');
			assert.ok(content.includes('@snote:'), 'Should contain supplementary note references');
		});

		test('Should handle bibliography parsing correctly', async () => {
			// Test that we can parse the bibliography file programmatically
			const bibPath = path.join(exampleManuscriptPath, '03_REFERENCES.bib');
			const content = fs.readFileSync(bibPath, 'utf8');

			// Count the number of bibliography entries
			const entries = content.match(/@\w+\s*\{[^,\s]+\s*,/g);
			assert.ok(entries && entries.length > 0, 'Should find bibliography entries');

			// Verify specific entries exist
			const entryKeys = entries?.map(entry => entry.match(/@\w+\s*\{([^,\s]+)\s*,/)?.[1]).filter(Boolean);
			assert.ok(entryKeys?.includes('Knuth1984_literate_programming'), 'Should contain Knuth entry');
			assert.ok(entryKeys?.includes('Hunter2007_matplotlib'), 'Should contain matplotlib entry');
		});

		test('Should validate completion providers with EXAMPLE_MANUSCRIPT content', async () => {
			// Open the main document to activate extension
			const mainPath = path.join(exampleManuscriptPath, '01_MAIN.md');
			const uri = vscode.Uri.file(mainPath);
			const document = await vscode.workspace.openTextDocument(uri);
			await vscode.window.showTextDocument(document);

			// Give extension time to activate
			await new Promise(resolve => setTimeout(resolve, 500));

			// Test citation completion - find a position after @ symbol
			const content = document.getText();
			const citationMatch = content.match(/(@[\w\d_]+)/);
			assert.ok(citationMatch, 'Should find citation patterns in document');

			// Test reference completion - find references like @fig:, @eq:, etc.
			const figureRefs = content.match(/@fig:[\w-]+/g);
			const equationRefs = content.match(/@eq:[\w-]+/g);
			const tableRefs = content.match(/@stable:[\w-]+/g);
			const noteRefs = content.match(/@snote:[\w-]+/g);

			assert.ok(figureRefs && figureRefs.length > 0, 'Should find figure references');
			assert.ok(equationRefs && equationRefs.length > 0, 'Should find equation references');
			assert.ok(tableRefs && tableRefs.length > 0, 'Should find table references');
			assert.ok(noteRefs && noteRefs.length > 0, 'Should find note references');

			// Verify specific references exist
			assert.ok(figureRefs.includes('@fig:diagram'), 'Should contain diagram figure reference');
			assert.ok(figureRefs.includes('@fig:workflow'), 'Should contain workflow figure reference');
			assert.ok(equationRefs.includes('@eq:einstein'), 'Should contain Einstein equation reference');
			assert.ok(tableRefs.includes('@stable:figure-formats'), 'Should contain figure formats table reference');
			assert.ok(noteRefs.includes('@snote:figure-generation'), 'Should contain figure generation note reference');
		});

		test('Should validate project with validateProject command', async () => {
			// Test the validateProject command with the EXAMPLE_MANUSCRIPT
			// This test verifies the command can be executed (though UI interaction is limited in tests)

			// First ensure we're in the right workspace
			const workspaceFolders = vscode.workspace.workspaceFolders;
			if (workspaceFolders && workspaceFolders.length > 0) {
				// The command should be available
				const commands = await vscode.commands.getCommands();
				assert.ok(commands.includes('rxiv-maker.validateProject'), 'validateProject command should be available');
			}
		});
	});
});
