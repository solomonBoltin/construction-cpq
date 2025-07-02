
// Keep vite_ prefix cause vite maps only to env variables that start with vite_
const VITE_CUSTOM_API_DOMAIN = import.meta.env.VITE_CUSTOM_API_DOMAIN || ""; 
console.log("VITE_CUSTOM_API_DOMAIN:", VITE_CUSTOM_API_DOMAIN);

// Constructing the API base URL from custom domain or defaulting to the frontends domain by leaving it empty
export const API_BASE_URL = (VITE_CUSTOM_API_DOMAIN || "" ) + "/api/v1"; // From user plan
console.log("API_BASE_URL:", API_BASE_URL);

export const DEFAULT_QUOTE_CONFIG_ID = 1;

export const FenceCategoryType = "fence"; // for getting categories by type 
export const GateCategoryType = "gate";
export const AddonCategoryType = "additional"; // from mockup categories

export const MOCKUP_DEFAULT_IMAGE = "https://placehold.co/400x300/e2e8f0/64748b?text=Image";