const timeZoneOffset = -4;
const forumSessionData = [
    ['Ask Me Anything', 'LINK HERE', new Date(Date.UTC(2024, 8, 3, 16 + timeZoneOffset, 5, 0))],
    ['AI and Accessibility', 'LINK HERE', new Date(Date.UTC(2024, 8, 4, 10 + timeZoneOffset, 5, 0))],
    ['Deaf Hub at RIT', 'LINK HERE', new Date(Date.UTC(2024, 8, 6, 12 + timeZoneOffset, 5, 0))],
    ['Sonification', 'LINK HERE', new Date(Date.UTC(2024, 8, 10, 15 + timeZoneOffset, 5, 0))],
    ['SciELO y Accessibilidad', 'LINK HERE', new Date(Date.UTC(2024, 8, 11, 11 + timeZoneOffset, 5, 0))], // 17 CEST is 11 EST right?
    ['HTML Papers on arXiv', 'LINK HERE', new Date(Date.UTC(2024, 8, 12, 20 + timeZoneOffset, 5, 0))],
    ['Disability Models', 'LINK HERE', new Date(Date.UTC(2024, 8, 13, 12 + timeZoneOffset, 5, 0))],
];

const getFormattedDate = (date) => {
    var year = date.getFullYear();
    
    var month = (1 + date.getMonth()).toString();
    month = month.length > 1 ? month : '0' + month;
    
    var day = date.getDate().toString();
    day = day.length > 1 ? day : '0' + day;

    const estHours = (date.getHours() - 2 * timeZoneOffset);
    
    return month + '/' + day + '/' + year + ', ' + (estHours % 12) + `:00${estHours > 12 ? 'PM' : 'AM'} EST`;
}

const displayCurrentData = () => {
    const title_node = document.querySelector('#forum-session-title');
    const join_link_small = document.querySelector('#forum-session-link-small');
    const join_link_box = document.querySelector('#forum-session-link-box');
    const now = new Date();
    let set = false;

    forumSessionData.forEach(session => {
        if (!set) {
            const [title, link, start_time] = session;
            if (now < start_time) {
                title_node.textContent = `Coming up next: ${title} at ${getFormattedDate(start_time)}`;
                join_link_small.innerHTML = '<a href="https://cornell.ca1.qualtrics.com/jfe/form/SV_eEZ1d27LF2fVM7Y" target="_blank">Signup</a> or watch this space for the join link';
                join_link_box.innerHTML = '<a class="banner_link banner-btn-grad" target="_blank" href="https://accessibility2024.arxiv.org/schedule"><b>View Schedule</b></a>';
                set = true;
            }
            else if (now > start_time && now < new Date(start_time.getTime() + (55 * 60 * 1000))) {
                title_node.textContent = `Happening now: ${title} at ${getFormattedDate(start_time)}`;
                join_link_small.innerHTML = `<a href="${link}" target="_blank">Click here to join the session</a>. No registration required.`;
                join_link_box.innerHTML = `<a class="banner_link banner-btn-grad" target="_blank" href="${link}"><b>Join Session</b></a>`;
                set = true;
            }
        }
    });
}

displayCurrentData();