// 🔑 Keyword detection
const MAIN_STAT_KEYWORDS = {
  STR: ['Knight', 'Warrior', 'Axe', 'Hammer', 'Spear', 'Sword', 'Saber', 'Ellaha', 'Pile God', 'Desperado', 'Hellslayer', 'Bladecaster', 'Katana', 'Polearm', 'Siege', 'Knuckle', 'Cannon'],
  INT: ['Mage', 'Magician', 'Dunwitch', 'Shining Rod', 'Psy-limiter', 'Gauntlet', 'Wand', 'Staff', 'Fan', 'Summoner'],
  DEX: ['Archer', 'Ranger', 'Bow', 'Crossbow', 'Bowguns', 'Whispershot', 'Pistol', 'Soul Shooter'],
  LUK: ['Thief', 'Assassin', 'Dagger', 'Guards', 'Cane', 'Chain', 'Ritual', 'Chakram', 'Blade Lord']
};

const ALL_WEAPON_KEYWORDS = [
  ...MAIN_STAT_KEYWORDS.STR,
  ...MAIN_STAT_KEYWORDS.INT,
  ...MAIN_STAT_KEYWORDS.DEX,
  ...MAIN_STAT_KEYWORDS.LUK
];

const MATT_WEAPON_KEYWORDS = [
  'Shining Rod', 'Psy-limiter', 'Gauntlet', 'Wand', 'Staff', 'Fan', 'Summoner'
];

// 🔢 Flame Tiers
const MAIN_STAT_TIERS = [
  { min: 0, max: 19, values: [1, 2, 3, 4, 5, 6, 7] },
  { min: 20, max: 39, values: [2, 4, 6, 8, 10, 12, 14] },
  { min: 40, max: 59, values: [3, 6, 9, 12, 15, 18, 21] },
  { min: 60, max: 79, values: [4, 8, 12, 16, 20, 24, 28] },
  { min: 80, max: 99, values: [5, 10, 15, 20, 25, 30, 35] },
  { min: 100, max: 119, values: [6, 12, 18, 24, 30, 36, 42] },
  { min: 120, max: 139, values: [7, 14, 21, 28, 35, 42, 49] },
  { min: 140, max: 159, values: [8, 16, 24, 32, 40, 48, 56] },
  { min: 160, max: 179, values: [9, 18, 27, 36, 45, 54, 63] },
  { min: 180, max: 199, values: [10, 20, 30, 40, 50, 60, 70] },
  { min: 200, max: 229, values: [11, 22, 33, 44, 55, 66, 77] },
  { min: 230, max: Infinity, values: [12, 24, 36, 48, 60, 72, 84] }
];

const BOSS_TIERS = [2, 4, 6, 8, 10, 12, 14];
const ALL_STAT_TIERS = [1, 2, 3, 4, 5, 6, 7];

// 🔥 Weapon ATT/MATT Flame Tiers

const ABSOLAB_TIERS = {
  103: [16, 23, 32, 42, 53],
  143: [22, 32, 44, 58, 74],
  150: [23, 33, 46, 60, 77],
  151: [23, 34, 46, 61, 78],
  154: [24, 34, 47, 62, 79],
  184: [28, 41, 56, 74, 95],
  192: [29, 43, 59, 77, 99],
  197: [30, 44, 60, 79, 101],
  205: [31, 46, 63, 82, 106],
  210: [32, 47, 64, 84, 108],
  241: [37, 54, 73, 97, 124],
  245: [37, 54, 75, 98, 126]
};

const ARCANE_TIERS = {
  149: [27, 40, 55, 72, 92],
  206: [38, 55, 75, 99, 127],
  216: [39, 58, 79, 104, 133],
  218: [40, 58, 80, 105, 135],
  221: [40, 59, 81, 106, 136],
  264: [48, 70, 96, 127, 163],
  276: [50, 73, 101, 133, 170],
  283: [51, 75, 103, 136, 175],
  295: [54, 78, 108, 142, 182],
  302: [55, 80, 110, 145, 186],
  347: [63, 92, 126, 167, 214],
  353: [64, 94, 129, 170, 218]
};

const GENESIS_TIERS = {
  172: [31, 46, 63, 83, 106],
  237: [43, 63, 87, 114, 146],
  249: [45, 66, 91, 120, 154],
  251: [46, 67, 92, 121, 155],
  255: [46, 68, 93, 123, 157],
  304: [55, 81, 111, 146, 187],
  318: [58, 84, 116, 153, 196],
  326: [59, 87, 119, 157, 201],
  337: [61, 89, 123, 162, 208],
  340: [62, 90, 124, 163, 210],
  342: [62, 91, 125, 164, 211],
  348: [63, 92, 127, 167, 214],
  400: [72, 106, 146, 192, 246],
  406: [74, 108, 148, 195, 250]
};

module.exports = {
  MAIN_STAT_KEYWORDS,
  ALL_WEAPON_KEYWORDS,
  MATT_WEAPON_KEYWORDS,
  MAIN_STAT_TIERS,
  BOSS_TIERS,
  ALL_STAT_TIERS,
  ABSOLAB_TIERS,
  ARCANE_TIERS,
  GENESIS_TIERS
};
