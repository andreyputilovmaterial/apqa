import { markerClass } from './grouping';

// Shared message for the derived `unfinished` mark. Used both as the helper text
// under a rule's name and as the unfinished badge's hover tooltip.
export const UNFINISHED_MESSAGE =
  'This rule is marked “unfinished” and will not run until its left side, comparison, and right side are all filled in.';

// Inline row of short mark badges. `skip`/`xfail` render as plain badges; the
// derived `unfinished` badge additionally carries a `title` tooltip explaining
// what it means. Renders nothing (and takes no space) when there are no marks.
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
    :title="mark === 'unfinished' ? unfinishedMessage : undefined"
  >{{ mark }}</span>
</span>
`,

  setup() {
    return {
      unfinishedMessage: UNFINISHED_MESSAGE,
      markClass: markerClass,
    };
  },
};

export default MarksBadges;
