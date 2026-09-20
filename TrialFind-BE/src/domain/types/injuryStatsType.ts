export type InjuryStats = {
    totalInjuries: number;
    injuriesByType: {
        muscle: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
        articular: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
        other: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
    };
    injuriesByMatchType: {
        officialMatch: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
        };
        training: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
        };
        friendlyMatch: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
        };
    };
    totalRestDays: number;
    // players: PlayerInjuryDetails[];
};

export type PlayerInjuryDetails = {
    playerId: string;
    playerName: string;
    position: string;
    injuryCount: number;
    totalRestDays: number;
    injuries: {
        injuryName:string;
        injuryType: string;
        injuryDegree: string;
        matchType: string;
        restDays: number;
        startDate: Date | null;
        endDate: Date | null;
    }[];
};




export type PlayerInjuryStats = {
    playerId: string;
    playerName: string;
    position: string;
    totalInjuries: number;
    totalRestDays: number;
    injuriesByType: {
        muscle: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
        articular: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
        other: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
    };
    injuriesByMatchType: {
        officialMatch: { total: number; severe: number; moderate: number; minor: number };
        training: { total: number; severe: number; moderate: number; minor: number };
        friendlyMatch: { total: number; severe: number; moderate: number; minor: number };
    };
    injuriesByName: {
        [key: string]: {
            total: number;
            severe: number;
            moderate: number;
            minor: number;
            byMatchType: {
                officialMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                training: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
                friendlyMatch: {
                    severe: { total: number; players: PlayerInjuryDetails[] };
                    moderate: { total: number; players: PlayerInjuryDetails[] };
                    minor: { total: number; players: PlayerInjuryDetails[] };
                };
            };
        };
    };
    injuries: {
        injuryName: string;
        injuryType: string;
        injuryDegree: string;
        matchType: string;
        restDays: number;
        startDate: Date | null;
        endDate: Date | null;
    }[];
};

