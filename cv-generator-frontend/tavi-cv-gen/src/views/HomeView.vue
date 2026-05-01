<template>
  <CVForm />
</template>

<script>
import { defineComponent } from 'vue';

// Components
import CVForm from '../components/CVForm.vue';

export default defineComponent({
  name: 'HomeView',

  components: {
    CVForm,
  },
});
</script>
