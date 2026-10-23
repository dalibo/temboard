<script setup>
// Component to wrap a button to redirect to instance explain view with posted query
function explain(query) {
  const form = document.createElement("form");
  form.action = explainUrl;
  form.method = "POST";
  const input = document.createElement("input");
  input.name = "query";
  input.value = JSON.stringify(query);
  form.appendChild(input);
  document.body.appendChild(form);
  form.submit();
  document.body.removeChild(form);
}
</script>

<template>
  <slot :explain="explain" />
</template>
