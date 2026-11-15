import { computed } from 'vue';

export function makeCmdletArg(form) {
  return {
    props: {
      name: { type: String, required: true },
      value: { default: undefined },
      type: { type: String, default: 'text' },
    },

    setup(props) {
      const isFlag = computed(() => props.value === true);
      const valueComponent = computed(() =>
        `component-cmdlet-arg-${props.type || 'text'}-${form}`,
      );
      return { isFlag, valueComponent };
    },

    template: `
<span class="apqa-cmdlet-part">
  <template v-if="isFlag">{{ name }}</template>
  <template v-else><span class="apqa-cmdlet-arg-equals">{{ name }}=</span><component :is="valueComponent" :value="value" /></template>
</span>
`,
  };
}
