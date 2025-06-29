export const shortUnitType = (unitName: string | null | undefined): string => {
    if (!unitName) {
        return 'item';
    }
    const lowerUnitName = unitName.toLowerCase();
    switch (lowerUnitName) {
        case 'linear foot':
        case 'linear feet':
            return 'LF';
        case 'square foot':
        case 'square feet':
            return 'sq ft';
        case 'cubic foot':
        case 'cubic feet':
            return 'cu ft';
        case 'each':
        case 'none':
            return 'item';
        default:
            // if it's a short form already, return it
            if (unitName.length <= 4) {
                return unitName;
            }
            // basic abbreviation
            const words = unitName.split(' ');
            if (words.length > 1) {
                return words.map(w => w[0]).join('');
            }
            return unitName;
    }
};
