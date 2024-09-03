const timeZoneOffset = -4;
const forumSessionData = [
    ['Ask Me Anything', 'https://cornell.zoom.us/j/98545128980?pwd=nTqDO00SOxW6ThtbYPFRSbbA57aWYM.1', new Date(Date.UTC(2024, 8, 3, 16 - timeZoneOffset, 0, 0))],
    ['AI and Accessibility', 'https://cornell.zoom.us/j/93724730382?pwd=qealqZFZRu1qdVzEFFYbUl94fPiamw.1', new Date(Date.UTC(2024, 8, 4, 12 - timeZoneOffset, 0, 0))],
    ['Deaf Hub at RIT', 'https://cornell.zoom.us/j/95831073771?pwd=Abdx2xsJanNwGS7UL4dxQVn9sQpojr.1', new Date(Date.UTC(2024, 8, 6, 12 - timeZoneOffset, 0, 0))],
    ['Sonification', 'https://cornell.zoom.us/j/95303704836?pwd=bnIanuPLl7mJvdHGIq5VDsdiEhhuYT.1', new Date(Date.UTC(2024, 8, 10, 15 - timeZoneOffset, 0, 0))],
    ['SciELO y Accessibilidad', 'https://cornell.zoom.us/j/95978099995?pwd=TLFRHtobdTSpwJLDInZ8GNgVEFWUPB.1', new Date(Date.UTC(2024, 8, 11, 11 - timeZoneOffset, 0, 0))], // 17 CEST is 11 EST right?
    ['HTML Papers on arXiv', 'https://cornell.zoom.us/j/92772646280?pwd=nN9qJXOPnDZ9kdFUsVYDciuL5M4oXA.1', new Date(Date.UTC(2024, 8, 12, 20 - timeZoneOffset, 0, 0))],
    ['Universal Designs for Research', 'https://cornell.zoom.us/j/94263795591?pwd=2cni3kKjJiYHykTfAooNCIyYxTPB2p.1', new Date(Date.UTC(2024, 8, 13, 12 - timeZoneOffset, 0, 0))],
];

const getFormattedDate = (date) => {
    let options = { timeZone: 'America/New_York', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric' };
    let etcDate = new Intl.DateTimeFormat('en-US', options).format(date);
  
    return etcDate + " EST";
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
                title_node.textContent = `COMING UP NEXT: ${title} Session at ${getFormattedDate(start_time)}`;
                join_link_small.innerHTML = '<a href="https://cornell.ca1.qualtrics.com/jfe/form/SV_eEZ1d27LF2fVM7Y" target="_blank">Sign up</a> or watch this space for the join link';
                join_link_box.innerHTML = '<a class="banner_link banner-btn-grad" target="_blank" href="https://accessibility2024.arxiv.org/schedule"><b>View Schedule</b></a>';
                set = true;
            }
            else if (now > start_time && now < new Date(start_time.getTime() + (55 * 60 * 1000))) {
                title_node.textContent = `HAPPENING NOW: ${title} Session at ${getFormattedDate(start_time)}`;
                join_link_small.innerHTML = `<a href="${link}" target="_blank">Click here to join the session</a>. No registration required.`;
                join_link_box.innerHTML = `<a class="banner_link banner-btn-grad" target="_blank" href="${link}"><b>Join Session</b></a>`;
                set = true;
            }
        }
    });
}

displayCurrentData();
