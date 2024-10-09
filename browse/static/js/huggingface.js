// Labs integration for displaying machine learning demos from huggingface.co

(function () {
    const container = document.getElementById("huggingface-output");
    const containerAlreadyHasContent = container.innerHTML.trim().length > 0;

    // This script is invoked every time the Labs toggle is toggled, even when
    // it's toggled to disabled. So this check short-circuits the script if the
    // container already has content.
    if (containerAlreadyHasContent) {
        container.innerHTML = "";
        container.setAttribute("style", "display:none");
        return;
    } else {
        container.setAttribute("style", "display:block");
    }

    // Get the arXiv paper ID from the URL, e.g. "2103.17249"
    // (this can be overridden for testing by passing a override_paper_id query parameter in the URL)
    const params = new URLSearchParams(document.location.search);
    const arxivPaperId = params.get("override_paper_id") || window.location.pathname.split('/').reverse()[0];
    if (!arxivPaperId) return;

    const huggingfaceApiHost = "https://huggingface.co/api";
    const huggingfaceRepo = `${huggingfaceApiHost}/arxiv/${arxivPaperId}/repos`;
    const huggingfacePaperApi = `${huggingfaceApiHost}/papers/${arxivPaperId}`;

    const MAX_TAGS = 5; // maximum number of tags to show

    // Search the HF API for demos that cite this paper
    (async () => {
        try {
            // Fetch paper data
            let response = await fetch(huggingfacePaperApi);
            if (!response.ok) {
                console.error(`Unable to fetch data from ${huggingfacePaperApi}`);
                render(0, [], []);
                return;
            }

            let paper_data = await response.json();

            if (paper_data.hasOwnProperty("error")) {
                console.error(`Arxiv id has no paper associated`);
                render(0, [], []);
                return;
            } else {
                // Fetch repository data
                let repoResponse = await fetch(huggingfaceRepo);
                if (!repoResponse.ok) {
                    console.error(`Unable to fetch data from ${huggingfaceRepo}`);
                    render(0, [], []);
                    return;
                }

                let repo_data = await repoResponse.json();

                let models = [];
                let datasets = [];
                if (repo_data.hasOwnProperty("models")) {
                    models = repo_data.models;
                }
                if (repo_data.hasOwnProperty("datasets")) {
                    datasets = repo_data.datasets;
                }
                render(1, models, datasets);
            }
        } catch (error) {
            console.error(`Error fetching data: ${error}`);
            render(0, [], []);
        }
    })();

    // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
    function render(status, models, datasets) {
        container.innerHTML = window.DOMPurify.sanitize(`
            ${summary(status)}
            ${renderModels(models, datasets)}
        `);
    }

    function summary(status) {
        let message = '';
        switch (status) {
            case 0:
                message = `The 🤗 paper page does not exist for this article. You can <a href="https://huggingface.co/papers/index?arxivId=${arxivPaperId}">index it here</a>.`;
                break;
            case 1:
                message = `The 🤗 paper page for this article is available <a href="https://huggingface.co/papers/${arxivPaperId}">here</a>.`;
                break;
            default:
                message = `The 🤗 paper page does not exist for this article. You can <a href="https://huggingface.co/papers/index?arxivId=${arxivPaperId}">index it here</a>.`;
                break;
        }
        // Wrapped the message in a div for better control over styling
        return `<div class="paper-summary">
                    <div class="huggingface-section">
                        <h3>Paper</h3>
                        <p>${message}</p>
                    </div>
                </div>`;
    }

    function renderModels(models, datasets) {
        let html = '';

        // Render Models
        if (models.length > 0) {
            html += `
                <div class="huggingface-section">
                    <h3>Models</h3>
                    <div class="huggingface-items">
            `;

            models.forEach(model => {
                html += `
                    <div class="huggingface-item">
                        <div class="hf-item-content">
                            <h4><a href="https://huggingface.co/${model.id}" target="_blank">${model.id}</a></h4>
                            <p>Author: <a href="https://huggingface.co/${encodeURIComponent(model.author)}" target="_blank">${model.author}</a></p>
                            <p>👍 ${model.likes} | Downloads: ${model.downloads}</p>
                            <p>Last Modified: ${formatDate(model.lastModified)}</p>
                            <div class="tags">
                                ${renderTags(model.tags)}
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        // Render Datasets
        if (datasets.length > 0) {
            html += `
                <div class="huggingface-section">
                    <h3>Datasets</h3>
                    <div class="huggingface-items">
            `;

            datasets.forEach(dataset => {
                const filteredTags = dataset.tags.filter(tag => !tag.startsWith("size_categories"));
                html += `
                    <div class="huggingface-item">
                        <div class="hf-item-content">
                            <h4><a href="https://huggingface.co/datasets/${dataset.id}" target="_blank">${dataset.id}</a></h4>
                            <p>Author: <a href="https://huggingface.co/${encodeURIComponent(dataset.author)}" target="_blank">${dataset.author}</a></p>
                            <p>👍 ${dataset.likes} | Downloads: ${dataset.downloads}</p>
                            <p>Last Modified: ${formatDate(dataset.lastModified)}</p>
                            <div class="tags">
                                ${renderTags(filteredTags)}
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        return html;
    }

    // Utility function to format dates with full month names
    function formatDate(dateString) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, options);
    }

    // Removed renderTags function as tags are no longer displayed
    function renderTags(tags) {
        if (!tags || tags.length === 0) return '';

        const displayedTags = tags.slice(0, MAX_TAGS);
        const remainingTags = tags.length - MAX_TAGS;

        let html = displayedTags.map(tag => `<span class="ant-tag">${tag}</span>`).join(' ');

//        if (remainingTags > 0) {
//            html += ` <span class="ant-tag more-tags">+${remainingTags} more</span>`;
//        }

        return html;
    }

    // Updated CSS: Removed all tag-related styles and increased the font size of the summary
    const style = document.createElement('style');
    style.innerHTML = `
        .huggingface-section {
            margin: 20px 0;
        }
        .huggingface-section h3 {
            font-size: 1.4em; /* Reduced font size for better balance */
            margin-bottom: 10px;
            color: #333;
        }
        .hf-icon {
            width: 24px;
            height: 24px;
            margin-left: 10px;
        }
        .huggingface-items {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .huggingface-item {
            display: flex;
            align-items: flex-start;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            width: 300px;
            background-color: #f9f9f9;
            box-sizing: border-box;
            transition: box-shadow 0.3s;
        }
        .huggingface-item:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .hf-item-icon {
            width: 40px;
            height: 40px;
            margin-right: 10px;
            flex-shrink: 0;
        }
        .hf-item-content {
            flex: 1;
            min-width: 0; /* Ensures content doesn't overflow the container */
        }
        .hf-item-content h4 {
            margin: 0 0 5px 0;
            font-size: 1.1em; /* Reduced font size for better balance */
            word-break: break-word; /* Prevents long words from breaking layout */
            color: #007blac;
        }
        .hf-item-content h4 a {
            text-decoration: none;
            color: inherit;
        }
        .hf-item-content h4 a:hover {
            text-decoration: underline;
        }
        .hf-item-content p {
            margin: 2px 0;
            font-size: 0.9em;
            color: black;
            word-break: break-word; /* Ensures long text wraps properly */
        }
        .tags {
            margin-top: 5px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .ant-tag {
            display: inline-block;
            padding: 0 8px;
            height: 20px;
            font-size: 12px;
            line-height: 20px;
            color: grey;
            background-color: #f0f0f0;
            border: 1px solid #d9d9d9;
            border-radius: 2px;
            cursor: default;
            user-select: none;
            white-space: nowrap; /* Prevents tags from stretching vertically */
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100%; /* Ensures tag doesn't exceed container width */
        }
        .ant-tag.more-tags {
            background-color: #e6f7ff;
            border-color: #91d5ff;
            color: #096dd9;
            cursor: pointer;
        }
        .ant-tag:hover {
            background-color: #e6f7ff;
            border-color: #91d5ff;
        }
        .ant-tag:active {
            color: #096dd9;
            border-color: #40a9ff;
            background-color: #e6f7ff;
        }
        .paper-summary {
            margin-bottom: 15px;
            color: #333;
        }
        .paper-summary a {
            color: #007bff;
            text-decoration: none;
            font-weight: bold;
        }
        .paper-summary a:hover {
            text-decoration: underline;
        }

        /* Responsive Adjustments */
        @media (max-width: 768px) {
            .huggingface-item {
                width: 100%;
            }
            .spaces-summary {
                font-size: 1.2em; /* Slightly reduced on smaller screens */
            }
            .huggingface-section h3 {
                font-size: 1.2em;
            }
            .hf-item-content h4 {
                font-size: 1em;
            }
        }
    `;
    document.head.appendChild(style);
})();
