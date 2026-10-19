const repoPathInput = document.getElementById("repoPath");
const searchQueryInput = document.getElementById("searchQuery");
const contextLinesInput = document.getElementById("contextLines");

const searchButton = document.getElementById("searchButton");
const filesButton = document.getElementById("filesButton");
const statsButton = document.getElementById("statsButton");
const symbolsButton = document.getElementById("symbolsButton");
const dependenciesButton = document.getElementById("dependenciesButton");
const refreshButton = document.getElementById("refreshButton");

const summaryContainer = document.getElementById("summary");
const resultsContainer = document.getElementById("results");
const statusText = document.getElementById("statusText");
const fileDialog = document.getElementById("fileDialog");
const fileDialogTitle = document.getElementById("fileDialogTitle");
const fileDialogBody = document.getElementById("fileDialogBody");
const closeFileButton = document.getElementById("closeFileButton");

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function getRepoPath() {
    return repoPathInput.value.trim();
}


function getSearchQuery() {
    return searchQueryInput.value.trim();
}


function getContextLines() {
    return contextLinesInput.value;
}


function setStatus(message) {
    statusText.textContent = message;
}


function clearPage() {
    summaryContainer.innerHTML = "";
    resultsContainer.innerHTML = "";
}


function showError(message) {
    resultsContainer.innerHTML = `
        <div class="error-state">
            ${escapeHTML(message)}
        </div>
    `;
}



async function requestJSON(endpoint, params, options = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = `${endpoint}?${queryString}`;

    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || `Request failed with status ${response.status}`
        );
    }

    return data;
}



function renderSummary(cards) {
    summaryContainer.innerHTML = cards.map(card => {
        return `
            <article class="stat-card">
                <span>${escapeHTML(card.label)}</span>
                <strong>${escapeHTML(card.value)}</strong>
            </article>
        `;
    }).join("");
}

// Opens a source file in a popup window
async function openFile(filePath, focusLine = 1) {

    // Get the repository path from the input box
    const repoPath = getRepoPath();

    // Set the popup title to the selected filename
    fileDialogTitle.textContent = filePath;

    // Show a loading message
    fileDialogBody.textContent = "Loading file...";

    // Open the popup
    fileDialog.showModal();

    try {
        // Ask FastAPI for the contents of the selected file
        const data = await requestJSON("/file", {
            repo_path: repoPath,
            file_path: filePath,
        });

        // Convert every line of code into HTML
        fileDialogBody.innerHTML = data.lines.map(line => {

            // Check whether this line is the selected search result
            const isHighlighted = line.line_number === focusLine;

            return `
                <div class="file-code-line ${isHighlighted ? "highlighted" : ""}">

                    <span class="file-line-number">
                        ${line.line_number}
                    </span>

                    <code class="file-line-text">${escapeHTML(line.text)}</code>

                </div>
            `;

        }).join("");

        // Find the highlighted line
        const highlightedLine = fileDialogBody.querySelector(
            ".file-code-line.highlighted"
        );

        // Scroll to that line automatically
        if (highlightedLine) {
            highlightedLine.scrollIntoView({
                block: "center",
            });
        }

    } catch (error) {

        console.error("RepoLens file viewer error:", error);

        fileDialogBody.textContent =
            `Could not open file: ${error.message}`;
    }
}


function renderSearchResults(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Files scanned",
            value: data.files_scanned,
        },
        {
            label: "Lines scanned",
            value: data.lines_scanned,
        },
        {
            label: "Results found",
            value: data.results_found,
        },
    ]);

    if (data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No results found for "${escapeHTML(data.query)}".
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = data.results.map(result => {
        const contextHTML = result.context.map(contextLine => {
            const marker = contextLine.is_match ? ">" : "";

            return `
                <div class="code-line ${contextLine.is_match ? "match" : ""}">
                    <span class="marker">${marker}</span>
                    <span class="line-number">${contextLine.line_number}</span>
                    <span class="line-code">${escapeHTML(contextLine.line)}</span>
                </div>
            `;
        }).join("");

        return `
            <article class="result-card">

                <div class="result-path">
                    <span>
                        ${escapeHTML(result.path)}:${result.line_number}
                    </span>

                    <button
                        type="button"
                        class="open-file-button"
                        data-open-file="${escapeHTML(result.path)}"
                        data-line-number="${result.line_number}">
                        Open File
                    </button>
                </div>

                <div class="code-block">
                    ${contextHTML}
                </div>

            </article>
        `;
    }).join("");
}



function renderFiles(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Files found",
            value: data.files_found,
        },
    ]);

    if (data.files.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No supported files found.
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = `
        <div class="file-list">
            ${data.files.map(file => {
                return `
                    <div class="file-row">

                        <button
                            type="button"
                            class="file-open-link"
                            data-open-file="${escapeHTML(file.path)}"
                            data-line-number="1">

                            <code>${escapeHTML(file.path)}</code>

                        </button>

                        <span>${escapeHTML(file.line_count)} lines</span>

                    </div>
                `;
            }).join("")}
        </div>
    `;
}



function renderStats(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Files scanned",
            value: data.files_scanned,
        },
        {
            label: "Lines scanned",
            value: data.lines_scanned,
        },
    ]);

    resultsContainer.innerHTML = `
        <div class="empty-state">
            RepoLens scanned ${escapeHTML(data.files_scanned)} file(s)
            and ${escapeHTML(data.lines_scanned)} line(s) of code.
        </div>
    `;
}



function renderSymbols(data) {
    renderSummary([
        {
            label: "Repository",
            value: data.repository,
        },
        {
            label: "Python files",
            value: data.python_files_analyzed,
        },
        {
            label: "Symbols found",
            value: data.symbols_found,
        },
        {
            label: "Imports found",
            value: data.imports_found,
        },
    ]);

    if (data.files.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No Python files found to analyze.
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = data.files.map(file => {

        // Build clickable function and class names.
        const symbolsHTML = file.symbols.length === 0
            ? `<p class="muted-text">No functions or classes found.</p>`
            : file.symbols.map(symbol => {
                return `
                    <div class="symbol-row">

                        <span class="symbol-type">
                            ${escapeHTML(symbol.type)}
                        </span>

                        <button
                            type="button"
                            class="file-open-link"
                            data-open-file="${escapeHTML(file.path)}"
                            data-line-number="${symbol.line_number}">

                            <code>${escapeHTML(symbol.name)}</code>

                        </button>

                        <span>
                            Line ${symbol.line_number}
                        </span>

                    </div>
                `;
            }).join("");

        // Build clickable import statements.
        const importsHTML = file.imports.length === 0
            ? `<p class="muted-text">No imports found.</p>`
            : file.imports.map(importItem => {

                let importText;

                if (importItem.type === "from_import") {
                    const dots = ".".repeat(importItem.level || 0);
                    const module = importItem.module || "";

                    importText = `from ${dots}${module} import ${importItem.name}`;
                } else {
                    importText = `import ${importItem.module}`;
                }

                if (importItem.alias) {
                    importText += ` as ${importItem.alias}`;
                }

                return `
                    <div class="symbol-row">

                        <span class="symbol-type">
                            ${escapeHTML(importItem.type)}
                        </span>

                        <button
                            type="button"
                            class="file-open-link"
                            data-open-file="${escapeHTML(file.path)}"
                            data-line-number="${importItem.line_number}">

                            <code>${escapeHTML(importText)}</code>

                        </button>

                        <span>
                            Line ${importItem.line_number}
                        </span>

                    </div>
                `;
            }).join("");

        const parseErrorHTML = file.parse_error
            ? `<div class="error-state">
                Parse error: ${escapeHTML(file.parse_error)}
               </div>`
            : "";

        return `
            <article class="result-card">

                <div class="result-path">
                    ${escapeHTML(file.path)}
                </div>

                <div class="symbol-section">

                    ${parseErrorHTML}

                    <h3>Symbols</h3>
                    ${symbolsHTML}

                    <h3>Imports</h3>
                    ${importsHTML}

                </div>

            </article>
        `;
    }).join("");
}



function createSVGElement(tag, attributes = {}) {
    const element = document.createElementNS(
        "http://www.w3.org/2000/svg",
        tag
    );

    for (const [name, value] of Object.entries(attributes)) {
        element.setAttribute(name, String(value));
    }

    return element;
}


function renderDependencies(data) {
    renderSummary([
        { label: "Repository", value: data.repository },
        { label: "Python files", value: data.files_analyzed },
        { label: "Dependencies", value: data.dependencies_found },
    ]);

    if (data.nodes.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                No Python files were found.
            </div>
        `;
        return;
    }

    resultsContainer.innerHTML = `
        <div class="dependency-layout">
            <section class="dependency-graph-panel">
                <p class="muted-text">
                    Arrows point from a file to the file it imports.
                    Click a node to inspect its relationships.
                </p>

                <div class="dependency-canvas">
                    <svg id="dependencyGraph"
                         aria-label="Python dependency graph">
                    </svg>
                </div>
            </section>

            <aside id="dependencyDetails"
                   class="dependency-details"
                   aria-live="polite">
            </aside>
        </div>
    `;

    const svg = document.getElementById("dependencyGraph");
    const details = document.getElementById("dependencyDetails");

    // Build lookup tables for imported files and dependents.
    const knownIds = new Set(data.nodes.map(node => node.id));

    const edges = data.edges.filter(edge =>
        knownIds.has(edge.source) && knownIds.has(edge.target)
    );

    const imports = new Map();
    const usedBy = new Map();

    for (const node of data.nodes) {
        imports.set(node.id, []);
        usedBy.set(node.id, []);
    }

    for (const edge of edges) {
        imports.get(edge.source).push(edge.target);
        usedBy.get(edge.target).push(edge.source);
    }

    // Calculate graph layers.
    // Files with no imports go on the left.
    // Files importing other files appear farther right.
    const remaining = new Map();
    const layers = new Map();
    const queue = [];

    for (const node of data.nodes) {
        const count = imports.get(node.id).length;

        remaining.set(node.id, count);
        layers.set(node.id, 0);

        if (count === 0) {
            queue.push(node.id);
        }
    }

    for (let i = 0; i < queue.length; i++) {
        const completed = queue[i];

        for (const dependent of usedBy.get(completed)) {
            const nextLayer = layers.get(completed) + 1;

            layers.set(
                dependent,
                Math.max(layers.get(dependent), nextLayer)
            );

            remaining.set(dependent, remaining.get(dependent) - 1);

            if (remaining.get(dependent) === 0) {
                queue.push(dependent);
            }
        }
    }

    // Organize files into columns.
    const columns = new Map();

    for (const node of data.nodes) {
        const layer = layers.get(node.id);

        if (!columns.has(layer)) {
            columns.set(layer, []);
        }

        columns.get(layer).push(node.id);
    }

    // Determine node positions.
    const nodeWidth = 184;
    const nodeHeight = 52;
    const horizontalGap = 100;
    const verticalGap = 44;
    const padding = 30;

    const positions = new Map();

    let maxColumn = 0;
    let maxRows = 0;

    for (const [column, ids] of columns) {
        ids.sort();
        maxColumn = Math.max(maxColumn, column);
        maxRows = Math.max(maxRows, ids.length);

        ids.forEach((id, row) => {
            positions.set(id, {
                x: padding + column * (nodeWidth + horizontalGap),
                y: padding + row * (nodeHeight + verticalGap),
            });
        });
    }

    const width =
        padding * 2 +
        (maxColumn + 1) * nodeWidth +
        maxColumn * horizontalGap;

    const height = Math.max(
        220,
        padding * 2 +
        maxRows * nodeHeight +
        Math.max(0, maxRows - 1) * verticalGap
    );

    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    // Add an arrowhead definition.
    svg.innerHTML = `
        <defs>
            <marker id="dependencyArrow"
                    viewBox="0 0 10 10"
                    refX="9"
                    refY="5"
                    markerWidth="7"
                    markerHeight="7"
                    orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z"
                      fill="#9aa6bf" />
            </marker>
        </defs>
    `;

    // Draw connections before nodes so lines stay behind boxes.
    const edgeElements = [];

    for (const edge of edges) {
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);

        let startX;
        let startY;
        let endX;
        let endY;
        let pathData;

        if (source.x !== target.x) {
            const rightward = target.x > source.x;

            startX = rightward ? source.x + nodeWidth : source.x;
            endX = rightward ? target.x : target.x + nodeWidth;

            startY = source.y + nodeHeight / 2;
            endY = target.y + nodeHeight / 2;

            const middleX = (startX + endX) / 2;

            pathData = `
                M ${startX} ${startY}
                C ${middleX} ${startY},
                  ${middleX} ${endY},
                  ${endX} ${endY}
            `;
        } else {
            const downward = target.y > source.y;

            startX = source.x + nodeWidth / 2;
            endX = target.x + nodeWidth / 2;

            startY = downward ? source.y + nodeHeight : source.y;
            endY = downward ? target.y : target.y + nodeHeight;

            const middleY = (startY + endY) / 2;

            pathData = `
                M ${startX} ${startY}
                C ${startX} ${middleY},
                  ${endX} ${middleY},
                  ${endX} ${endY}
            `;
        }

        const path = createSVGElement("path", {
            d: pathData,
            class: "dependency-edge",
            "marker-end": "url(#dependencyArrow)",
        });

        svg.appendChild(path);
        edgeElements.push({ element: path, edge });
    }

    // Create clickable nodes for each Python file.
    const nodeElements = new Map();

    for (const node of data.nodes) {
        const position = positions.get(node.id);

        const group = createSVGElement("g", {
            class: "dependency-node",
            role: "button",
            tabindex: "0",
            "aria-label": `Inspect ${node.id}`,
        });

        const rectangle = createSVGElement("rect", {
            x: position.x,
            y: position.y,
            width: nodeWidth,
            height: nodeHeight,
            rx: 10,
        });

        const label = createSVGElement("text", {
            x: position.x + 12,
            y: position.y + 32,
        });

        const shortName = node.label.length > 24
            ? node.label.slice(0, 21) + "..."
            : node.label;

        label.textContent = shortName;

        const tooltip = createSVGElement("title");
        tooltip.textContent = node.id;

        group.appendChild(rectangle);
        group.appendChild(label);
        group.appendChild(tooltip);

        group.addEventListener("click", () => selectNode(node.id));

        group.addEventListener("keydown", event => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                selectNode(node.id);
            }
        });

        svg.appendChild(group);
        nodeElements.set(node.id, group);
    }

    // Display the relationships of the selected file.
    function selectNode(fileId) {
        const importedFiles = [...new Set(imports.get(fileId))].sort();
        const dependentFiles = [...new Set(usedBy.get(fileId))].sort();

        function makeList(items) {
            if (items.length === 0) {
                return `<p class="muted-text">None detected.</p>`;
            }

            return `
                <ul>
                    ${items.map(item =>
                        `<li><code>${escapeHTML(item)}</code></li>`
                    ).join("")}
                </ul>
            `;
        }

        details.innerHTML = `
            <h3>${escapeHTML(fileId)}</h3>

            <h4>Imports</h4>
            ${makeList(importedFiles)}

            <h4>Used by</h4>
            ${makeList(dependentFiles)}
        `;

        for (const [id, element] of nodeElements) {
            element.classList.toggle("selected", id === fileId);

            element.classList.toggle(
                "related",
                importedFiles.includes(id) || dependentFiles.includes(id)
            );
        }

        for (const item of edgeElements) {
            const related =
                item.edge.source === fileId ||
                item.edge.target === fileId;

            item.element.classList.toggle("highlighted", related);
        }
    }

    // Automatically select a useful node when opening the graph.
    const initialFile = edges.length > 0
        ? edges[0].target
        : data.nodes[0].id;

    selectNode(initialFile);
}



async function runSearch() {
    const repoPath = getRepoPath();
    const query = getSearchQuery();
    const contextLines = getContextLines();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    if (!query) {
        showError("Please enter a search query.");
        return;
    }

    clearPage();
    setStatus("Searching...");

    try {
        const data = await requestJSON("/search", {
            repo_path: repoPath,
            query: query,
            context_lines: contextLines,
        });

        renderSearchResults(data);
        setStatus("Search complete.");
    } catch (error) {
        showError(error.message);
        setStatus("Search failed.");
    }
}


async function viewFiles() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading files...");

    try {
        const data = await requestJSON("/files", {
            repo_path: repoPath,
        });

        renderFiles(data);
        setStatus("Files loaded.");
    } catch (error) {
        showError(error.message);
        setStatus("Could not load files.");
    }
}


async function viewStats() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading stats...");

    try {
        const data = await requestJSON("/stats", {
            repo_path: repoPath,
        });

        renderStats(data);
        setStatus("Stats loaded.");
    } catch (error) {
        showError(error.message);
        setStatus("Could not load stats.");
    }
}


async function viewSymbols() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading symbols...");

    try {
        const data = await requestJSON("/symbols", {
            repo_path: repoPath,
        });

        renderSymbols(data);
        setStatus("Symbols loaded.");
    } catch (error) {
        showError(error.message);
        setStatus("Could not load symbols.");
    }
}


async function viewDependencies() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    clearPage();
    setStatus("Loading dependencies...");

    try {
        const data = await requestJSON("/dependencies", {
            repo_path: repoPath,
        });

        renderDependencies(data);
        setStatus("Dependency graph loaded.");

    } catch (error) {
        console.error("RepoLens dependency error:", error);
        showError(error.message);
        setStatus("Could not load dependencies.");
    }
}


async function refreshRepository() {
    const repoPath = getRepoPath();

    if (!repoPath) {
        showError("Please enter a repository path.");
        return;
    }

    // Prevent repeated clicks while a refresh is in progress.
    refreshButton.disabled = true;

    setStatus("Refreshing repository...");

    try {
        // Ask FastAPI to clear its cache and scan the files again.
        const data = await requestJSON(
            "/refresh",
            { repo_path: repoPath },
            { method: "POST" }
        );

        console.log("Repository refreshed:", data);

        // Show updated search results using the fresh scan.
        if (getSearchQuery()) {
            await runSearch();
        } else {
            await viewFiles();
        }

    } catch (error) {
        console.error("RepoLens refresh error:", error);

        showError(error.message);
        setStatus("Could not refresh repository.");

    } finally {
        // Re-enable the button even if the request failed.
        refreshButton.disabled = false;
    }
}



searchButton.addEventListener("click", runSearch);
filesButton.addEventListener("click", viewFiles);
statsButton.addEventListener("click", viewStats);
symbolsButton.addEventListener("click", viewSymbols);
dependenciesButton.addEventListener("click", viewDependencies);
refreshButton.addEventListener("click", refreshRepository);

searchQueryInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        runSearch();
    }
});

// Listen for clicks on the Open File buttons
resultsContainer.addEventListener("click", event => {

    // Find the Open File button that was clicked
    const button = event.target.closest("[data-open-file]");

    // Stop if the click was not on an Open File button
    if (!button) {
        return;
    }

    // Get the file path from the button
    const filePath = button.dataset.openFile;

    // Get the line number from the button
    const lineNumber = Number(button.dataset.lineNumber);

    // Open the selected file
    openFile(filePath, lineNumber);
});


// Close the file viewer when the Close button is clicked
closeFileButton.addEventListener("click", () => {
    fileDialog.close();
});