<template>
  <div class="flex border-b pr-5 items-center gap-2">
    <div id="app-header" class="flex-1 w-full"></div>
    <div class="w-40 flex items-center self-center">
      <AgentStatusDropdown v-if="isAgent" />
    </div>
    <div class="flex items-center justify-center self-center">
      <CallUI :userEmail="user" />
    </div>
  </div>
</template>

<script setup>
import AgentStatusDropdown from "./AgentStatusDropdown.vue";
import CallUI from "@/components/telephony/CallUI.vue";
import { useAuthStore } from "@/stores/auth";
import { useTelephonyStore } from "@/stores/telephony";
import { onMounted } from "vue";

const { user, isAgent } = useAuthStore();

const telephonyStore = useTelephonyStore();

onMounted(() => {
  telephonyStore.fetchCallIntegrationStatus();
});
</script>
