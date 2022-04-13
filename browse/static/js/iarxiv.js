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
            <a href="/iarxiv_login">Signup</a>
            with IArxiv.org to receive paper recommendations by email for 
            astro-ph, hep-ph, hep-th and gr-qc. 
            Expanding to all subject categories soon!
        <div>
    `);
})();
