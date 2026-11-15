import { markerClass } from './grouping';

// Shared messages for the derived marks. Used both as the helper text under a
// rule's name and as the derived badge's hover tooltip.
export const UNFINISHED_MESSAGE =
  'This rule is marked “unfinished” and will not run until its left side, comparison, and right side are all filled in.';

export const INVALID_MESSAGE =
  'This rule is marked “invalid” and will fail when run: it references a cmdlet or comparison name this environment does not recognize.';

// Inline row of short mark badges. `skip`/`xfail` render as plain badges; the
// derived `unfinished`/`invalid` badges additionally carry a `title` tooltip
// explaining what they mean. Renders nothing (and takes no space) when there
// are no marks.
const MarksBadges = {
  props: {
    marks: { type: Array, default: () => [] },
  },

  template: `
<span v-if="marks.length" class="apqa-marks-badges">
  <span
    v-for="mark in marks"
    :key="mark"
    class="apqa-mark-badge"
    :class="'apqa-mark-badge-' + markClass(mark)"
    :title="markTooltip(mark)"
  >{{ mark }}</span>
</span>
`,

  setup() {
    function markTooltip(mark) {
      if (mark === 'unfinished') return UNFINISHED_MESSAGE;
      if (mark === 'invalid') return INVALID_MESSAGE;
      return undefined;
    }

    return {
      markTooltip,
      markClass: markerClass,
    };
  },
};

export default MarksBadges;
