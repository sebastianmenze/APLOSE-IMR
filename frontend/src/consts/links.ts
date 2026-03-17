export const GITHUB_URL = 'https://github.com/sebastianmenze/APLOSE-IMR';

export const CONTACT_MAIL = 'contact@oceansound.org';
export const CONTACT_URI = `mailto:${ CONTACT_MAIL }`;

export const DOWNLOAD_ANNOTATIONS_URL = (phaseID: string) => `/api/download/phase-annotations/${ phaseID }/`
export const DOWNLOAD_PROGRESS_URL = (phaseID: string) => `/api/download/phase-progression/${ phaseID }/`
