(function () {
    const $output = $('#iarxivOutput');
    if ($output.html() != '') {
        $output.html('');
        return;
    }

    $output.html(`
        <div style="clear:both"></div>
        <h3>IArxiv</h3>
        <div class="iarxiv">
            <a href="/iarxiv_login">Signup</a> with IArxiv.org to receive, by email, the daily Arxiv papers
            sorted according to your preferences in astro-ph, hep-ph, hep-th and gr-qc.
            Expanding to all subject categories soon!
            <br><br>
            <a href="/iarxiv_login" class="button-fancy">Signup with IArxiv <span></span></a>
        <div>
    `);
})();
