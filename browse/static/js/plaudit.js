(async function () {
  $output = $('#plauditContainer');
  const articleDoi = $output[0].dataset.doi;
  const articleTitleElementContent = document
    .querySelector("h1.title")
    .textContent;
  const articleTitle = articleTitleElementContent.startsWith("Title:")
    // The `h1.title` has a `span.description` preceding the title that just
    // says "Title:", so we'll need to strip that off:
    ? articleTitleElementContent.substring("Title:".length)
    : articleTitleElementContent;

  const endorsementsResponse = await fetch(
    `https://api.eventdata.crossref.org/v1/events?mailto=arxiv_integration@plaudit.pub&obj-id=${encodeURIComponent(`https://doi.org/${articleDoi}`)}&source=plaudit`
  );
  /**
   * @type {{
   *   status: "ok",
   *   "message-type": "event-list",
   *   message: {
   *     "total-results": number,
   *     events: Array<{
   *       obj_id: `https://doi.org/10.${string}`,
   *       subj_id:	`https://orcid.org/${string}`,
   *       occurred_at: string,
   *       source_id: "plaudit",
   *       action: "add",
   *     }>,
   *   },
   * }}
   */
  const endorsementsData = await endorsementsResponse.json();

  const endorsements = endorsementsData.message.events.filter(
    event => event.source_id === "plaudit" && event.action === "add",
  );

  const endorsementDescription = document.createElement("p");
  endorsementDescription.innerHTML = endorsements.length === 0
    ? `
      <a href="https://plaudit.pub/endorsements/doi:${articleDoi}" target="_blank" rel="noopener noreferrer">
        Be the first to endorse <b>${articleTitle}</b>.
      </a>`
    : `
      <a href="https://plaudit.pub/endorsements/doi:${articleDoi}" target="_blank" rel="noopener noreferrer">
        View ${endorsements.length} endorsement${endorsements.length > 0 && "s"} of <b>${articleTitle}</b>, or add your own.
      </a>`
  $output.append(endorsementDescription);
})();