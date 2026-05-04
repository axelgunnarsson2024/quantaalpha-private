/**
 * Reference mining directions list and default direction parsing (consistent with "Mining Direction" in settings)
 * Each direction can attach up to 3 factors' "short name", "expression", "meaning", displayed on hover
 */

export interface FactorHint {
  shortName: string;
  expression: string;
  meaning: string;
}

export interface MiningDirectionItem {
  label: string;
  /** Up to 3 factors, displayed when hovering over the direction */
  factors?: FactorHint[];
}

/** Reference mining directions (Alpha158(20) style, can be added/deleted/modified as needed; factors can be filled from original_direction.json) */
export const REFERENCE_MINING_DIRECTIONS: MiningDirectionItem[] = [
  {
    label: 'Price-Volume Relationship & Open Return',
    factors: [
      { shortName: 'KMID', expression: '(close-open)/open', meaning: 'Open return' },
      { shortName: 'KUP', expression: '(high-max(open,close))/open', meaning: 'Upper shadow vs open' },
      { shortName: 'KLOW', expression: '(min(open,close)-low)/open', meaning: 'Lower shadow vs open' },
    ],
  },
  { label: 'Short-term Momentum & Return', factors: [] },
  { label: 'Volume Ratio & Volume Surge Confirmation', factors: [] },
  { label: 'Volatility & Price Stability', factors: [] },
  { label: 'Amplitude & High-Low Range', factors: [] },
  { label: 'RSV & Overbought/Oversold', factors: [] },
  { label: 'Moving Average Ratio & Trend', factors: [] },
  { label: 'Shadow Ratio & Candlestick Patterns', factors: [] },
  { label: 'Body Ratio & Bull/Bear Strength', factors: [] },
  { label: 'Return Volatility & Risk', factors: [] },
  { label: 'High-Low Relative Position', factors: [] },
  { label: 'Price-Volume Divergence & Confirmation', factors: [] },
  { label: 'Multi-period Momentum Combination', factors: [] },
  { label: 'Normalized Volume Features', factors: [] },
  { label: 'Price Position Relative to Moving Average', factors: [] },
];

/** Get direction label (compatible with object or string) */
export function getDirectionLabel(item: MiningDirectionItem): string {
  return typeof item === 'string' ? item : item.label;
}

interface StoredMiningDirectionConfig {
  miningDirectionMode?: 'selected' | 'random';
  selectedMiningDirectionIndices?: number[];
}

/** Get a default mining direction from saved config (one of the selected list, or a random one) */
export function getDefaultMiningDirection(): string {
  try {
    const raw = localStorage.getItem('quantaalpha_config');
    if (!raw) return '';
    const config = JSON.parse(raw) as StoredMiningDirectionConfig;
    const indices = config?.selectedMiningDirectionIndices ?? [];
    const list = REFERENCE_MINING_DIRECTIONS;
    if (!list.length || !indices.length) return '';
    const validIndices = indices.filter((i) => i >= 0 && i < list.length);
    if (!validIndices.length) return '';
    if (config?.miningDirectionMode === 'random') {
      const idx = validIndices[Math.floor(Math.random() * validIndices.length)];
      return getDirectionLabel(list[idx]);
    }
    return getDirectionLabel(list[validIndices[0]]);
  } catch {
    return '';
  }
}
