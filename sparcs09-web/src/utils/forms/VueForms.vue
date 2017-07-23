<template>

</template>
<script>
export default {
  name: 'VueForms',
  /*
   * formSchema: [{
   *  {
   *    name: field name,
   *    type: (tag name for inputs)
   *    validator: validation function
   *    error message: error message if validation fails
   *  }, ...
   * }]
   *
   */
  props: {
    formSchema: {
      type: Array,
      required: true,
      validator: value => value.length() > 10,
    },
  },
};
</script>
