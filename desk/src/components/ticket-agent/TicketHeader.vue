<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex flex-col truncate">
        <Breadcrumbs :items="breadcrumbs" class="breadcrumbs">
          <template #prefix="{ item }">
            <Icon
              v-if="item.icon"
              :icon="item.icon"
              class="mr-1 h-4 flex items-center justify-center self-center"
            />
          </template>
        </Breadcrumbs>
        <TicketSLA />
      </div>
    </template>
    <template #right-header>
      <div class="flex gap-2 items-center">
        <MultipleAvatar
          :avatars="JSON.stringify(viewers)"
          size="md"
          :hide-name="true"
        />
        <TicketNavigation :key="ticket.name" />
        <div v-if="normalActions.length" class="flex gap-2">
          <Button v-for="action in normalActions" v-bind="action">
            <template v-if="action.icon" #prefix>
              <FeatherIcon :name="action.icon" class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <div v-if="groupedWithLabelActions.length">
          <div v-for="g in groupedWithLabelActions" :key="g.label">
            <Dropdown v-slot="{ open }" :options="g.action">
              <Button :label="g.label">
                <template #suffix>
                  <FeatherIcon
                    :name="open ? 'chevron-up' : 'chevron-down'"
                    class="h-4"
                  />
                </template>
              </Button>
            </Dropdown>
          </div>
        </div>
        <Dropdown
          v-if="groupedActions.length"
          :options="groupedActions"
          placement="right"
        >
          <Button icon="more-horizontal" />
        </Dropdown>
      </div>
    </template>
  </LayoutHeader>
  <TicketMergeModal
    :ticket="ticket.doc"
    v-if="showMergeModal"
    v-model="showMergeModal"
    @update="ticket.reload()"
  />
  <TicketSubjectModal v-if="showSubjectDialog" v-model="showSubjectDialog" />

  <Dialog v-model="showCloseDispositionModal" :options="{ size: '4xl' }">
    <template #body-title>
      <h3>{{ __("Close Ticket - Disposition") }}</h3>
    </template>
    <template #body-content>
      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">
            {{ __("Client Name") }}
          </label>
          <FormControl v-model="dispositionForm.client_name" type="text" />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">
            {{ __("Client Code") }}
          </label>
          <FormControl v-model="dispositionForm.client_code" type="text" />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">
            {{ __("Remarks") }} <span class="text-red-500">*</span>
          </label>
          <FormControl
            v-model="dispositionForm.remarks"
            type="textarea"
            :placeholder="__('Describe the full issue...')"
          />
        </div>

        <div>
          <div class="mb-1 flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">
              {{ __("Main Category") }}
            </label>
            <span
              v-if="isAutoDetectedCategory"
              class="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700"
            >
              {{ __("Auto-detected") }} &#10003;
            </span>
          </div>
          <FormControl
            v-model="dispositionForm.category"
            type="select"
            :options="mainCategoryOptions"
            @update:model-value="onManualMainCategoryChange"
          />
        </div>

        <div>
          <div class="mb-1 flex items-center gap-2">
            <label class="text-sm font-medium text-gray-700">
              {{ __("Sub Category") }}
            </label>
            <span
              v-if="isAutoDetectedSubCategory"
              class="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700"
            >
              {{ __("Auto-detected") }} &#10003;
            </span>
          </div>
          <FormControl
            v-model="dispositionForm.sub_category"
            type="select"
            :options="subCategoryOptions"
            :disabled="!dispositionForm.category"
            @update:model-value="onManualSubCategoryChange"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">
            {{ __("Disposition Type") }} <span class="text-red-500">*</span>
          </label>
          <FormControl
            v-model="dispositionForm.disposition_type"
            type="select"
            :options="dispositionTypeOptions"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        theme="green"
        :loading="isSubmittingDisposition"
        @click="submitDispositionAndClose"
      >
        {{ __("Submit & Close") }}
      </Button>
      <Button class="ml-2" @click="showCloseDispositionModal = false">
        {{ __("Cancel") }}
      </Button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { MultipleAvatar } from "@/components";
import LayoutHeader from "@/components/LayoutHeader.vue";
import TicketMergeModal from "@/components/ticket/TicketMergeModal.vue";
import { setupCustomizations } from "@/composables/formCustomisation";
import { useNotifyTicketUpdate } from "@/composables/realtime";
import { useView } from "@/composables/useView";
import { __ } from "@/translation";
import { globalStore } from "@/stores/globalStore";
import {
  ActivitiesSymbol,
  CustomizationSymbol,
  TicketSymbol,
  View,
} from "@/types";
import { getIcon } from "@/utils";
import { Breadcrumbs, call, Dialog, Dropdown, FormControl, toast } from "frappe-ui";
import {
  computed,
  ComputedRef,
  inject,
  PropType,
  reactive,
  ref,
  watch,
  watchEffect,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMerge from "~icons/lucide/merge";
import TicketNavigation from "./TicketNavigation.vue";
import TicketSLA from "./TicketSLA.vue";
import TicketSubjectModal from "./TicketSubjectModal.vue";

defineProps({
  viewers: {
    type: Array as PropType<string[]>,
    required: true,
  },
});

const route = useRoute();
const router = useRouter();
const { findView } = useView("HD Ticket");

const ticket = inject(TicketSymbol);
const customizations = inject(CustomizationSymbol);
const activities = inject(ActivitiesSymbol);

const showSubjectDialog = ref(false);
const showCloseDispositionModal = ref(false);
const isSubmittingDisposition = ref(false);
const isAutoDetectedCategory = ref(false);
const isAutoDetectedSubCategory = ref(false);

const categoryTree: Record<string, { keywords: string[]; subcategories: Record<string, string[]> }> = {
  "App Related Issue": {
    keywords: ["app", "application", "login", "crash", "bug", "error", "not working", "loading", "install", "routine", "chat", "store"],
    subcategories: {
      "Challenges with ROUTINE section": ["routine", "routine section", "challenges with routine"],
      "Fitelo Chat related Issue": ["chat", "fitelo chat", "message"],
      "Fitelo Store based queries": ["store", "fitelo store", "shop"],
      "Login Issue": ["login", "sign in", "password", "otp", "cannot login", "logout"],
    },
  },
  "CNR based Queries": {
    keywords: ["cnr", "call not received", "no response", "not reachable", "missed call"],
    subcategories: {
      "CNR query from client": ["client not reachable", "client cnr", "cnr from client"],
      "CNR request from dietitian": ["dietitian cnr", "dietitian not reachable", "cnr from dietitian"],
    },
  },
  "Commerce Related": {
    keywords: ["commerce", "order", "product", "delivery", "scale", "delivered"],
    subcategories: {
      "Commerce related GQ": ["commerce query", "commerce general"],
      "Product Delivered with Problems": ["delivered with problem", "damaged", "wrong product"],
      "Product Not Delivered": ["not delivered", "delivery pending", "not received product"],
      "Scale Related": ["scale", "weighing scale", "machine"],
    },
  },
  "Counseling Related": {
    keywords: ["counseling", "counselling", "session", "appointment", "reschedule", "book"],
    subcategories: {
      "Counselling Missed by the client": ["missed by client", "client missed", "client did not attend"],
      "Counselling Missed by the dietitian": ["missed by dietitian", "dietitian missed", "dietitian did not attend"],
      "Counselling Missed: Incomplete data on Panel": ["incomplete data", "panel data", "missing data"],
      "Counselling Missed: Manual counselling form related issue": ["manual form", "counselling form", "form issue"],
      "Counselling Missed: Others": ["counselling others", "other reason missed"],
      "Counselling Missed: Wrong assignment of dietitian": ["wrong assignment", "wrong dietitian assigned"],
      "Unable to book counselling on App": ["unable to book", "cannot book", "booking issue"],
      "Unable to reschedule counseling through the app": ["reschedule", "cannot reschedule", "reschedule issue"],
      "Wants to re-confirm booked counselling": ["reconfirm", "re-confirm", "confirm session"],
    },
  },
  "Diet Based Concerns": {
    keywords: ["diet", "meal", "food", "nutrition", "meal plan", "diet plan", "plan publish"],
    subcategories: {
      "Delay in plan publish": ["delay", "plan not published", "publish late", "plan delay"],
      "Follow up missed by the dietitian": ["follow up missed", "dietitian follow up", "no follow up"],
      "Meal preferences are not catered": ["meal preference", "food preference", "not catered", "preference ignored"],
    },
  },
  "Dietitian Compatibility": {
    keywords: ["dietitian change", "change dietitian", "different dietitian", "bond", "motivation", "expectation"],
    subcategories: {
      "Lack of Expectation Setting": ["expectation", "not meeting expectations", "lack of expectation"],
      "Missing Bond & Motivation": ["bond", "motivation", "no connection", "no rapport"],
      "Seeking dietitian change": ["change dietitian", "want different dietitian", "switch dietitian"],
    },
  },
  "Fitelo Commerce Related": {
    keywords: ["fitelo product", "fitelo store", "fitelo order", "fitelo commerce"],
    subcategories: {
      "Product Delivered with Problems": ["delivered with problem", "damaged fitelo", "wrong fitelo product"],
      "Product Not Delivered": ["fitelo product not delivered", "fitelo delivery pending"],
      "Product Related General Query": ["fitelo product query", "product question"],
      "Product Related Miscellaneous Issues": ["fitelo misc", "other product issue"],
    },
  },
  "Follow up and coordination related": {
    keywords: ["follow up", "followup", "no reply", "late reply", "coordination", "leave", "on leave"],
    subcategories: {
      "Challenges with sales representative": ["sales", "sales representative", "sales challenge"],
      "Client has preferred time to connect": ["preferred time", "time to connect", "client timing"],
      "Customer Support Related": ["customer support", "support issue", "helpdesk"],
      "Dietitian is on Leave(s)": ["on leave", "dietitian leave", "dietitian absent"],
      "First diet published was not intimated to the client": ["first diet", "not intimated", "diet not shared"],
      "Follow up missed by the dietitian": ["follow up missed", "missed follow up", "no follow up"],
      "No/late reply from Dietitian": ["no reply", "late reply", "dietitian not responding", "slow response"],
    },
  },
  "General Query": {
    keywords: ["query", "question", "general", "hair", "skin", "recipe", "referral", "social media", "warranty"],
    subcategories: {
      "Diet related general query": ["diet query", "diet question", "diet general"],
      "Dietitian related general query": ["dietitian query", "dietitian question"],
      "Doctor related": ["doctor", "physician", "medical advice"],
      "Hair & Skin related Queries": ["hair", "skin", "hair loss", "skin issue"],
      "Other businesses related queries": ["other business", "other query"],
      "Recipe related queries": ["recipe", "food recipe", "meal recipe"],
      "Referral related queries": ["referral", "refer", "referral code"],
      "Social Media Related": ["social media", "instagram", "facebook", "youtube"],
      "Warranty Related": ["warranty", "guarantee", "warranty issue"],
      "Wellness related general query": ["wellness query", "wellness question", "wellness general"],
    },
  },
  "Missed counselling": {
    keywords: ["missed counselling", "wrong assignment dietitian"],
    subcategories: {
      "Wrong assignment of dietitian": ["wrong assignment", "wrong dietitian", "incorrect assignment"],
    },
  },
  "NA": {
    keywords: ["na", "not applicable"],
    subcategories: {
      "NA": ["na"],
    },
  },
  "Out of Scope Services": {
    keywords: ["out of scope", "not covered", "cannot help", "outside scope"],
    subcategories: {
      "NA": ["out of scope", "not covered"],
    },
  },
  "Pause Facility": {
    keywords: ["pause", "resume", "hold", "suspend", "pause plan"],
    subcategories: {
      "Pause Refused": ["pause refused", "pause rejected", "cannot pause"],
      "Pause Request by Client": ["client wants pause", "pause request client", "client pause"],
      "Pause Request by Dietitian": ["dietitian pause", "pause by dietitian"],
      "Resume Request by Client": ["resume client", "client wants resume", "restart plan client"],
      "Resume Request by Dietitian": ["resume dietitian", "dietitian wants resume"],
    },
  },
  "Payment and subscription based queries": {
    keywords: ["payment", "subscription", "billing", "invoice", "emi", "upgrade", "swap", "plan cost", "renewal"],
    subcategories: {
      "Client wants to purchase/upgrade the plan": ["purchase", "upgrade", "buy plan", "new plan"],
      "Client wants to swap services": ["swap", "change service", "switch service"],
      "Confirmation on plan inclusives": ["plan inclusive", "what is included", "plan details"],
      "Discrepancy in subscription details": ["discrepancy", "wrong subscription", "subscription error"],
      "EMI based queries": ["emi", "installment", "emi query"],
      "Out of scope services committed": ["committed out of scope", "promised service", "false promise"],
      "Partial payment related": ["partial payment", "part payment", "incomplete payment"],
      "Payment Related": ["payment failed", "payment issue", "transaction failed"],
      "Transfer of plan": ["transfer plan", "plan transfer", "shift plan"],
    },
  },
  "Refund Requests by clients": {
    keywords: ["refund", "money back", "return money", "cancel", "hectic", "medical", "personal reason"],
    subcategories: {
      "Seeks refund due to hectic schedule": ["hectic schedule", "busy schedule", "no time"],
      "Seeks refund due to medical concerns": ["medical", "health issue", "doctor advised", "medical reason"],
      "Seeks refund due to personal reasons": ["personal reason", "personal issue", "family reason"],
    },
  },
  "Suggestions/Feedback by clients": {
    keywords: ["suggestion", "feedback", "improve", "review", "complaint"],
    subcategories: {
      "NA": ["suggestion", "feedback", "complaint", "review"],
    },
  },
  "Tools Related Issue": {
    keywords: ["tools", "smartwatch", "smart watch", "weight measurement", "tracker"],
    subcategories: {
      "Others": ["tool others", "other tool issue"],
      "Smart watch related": ["smartwatch", "smart watch", "watch issue", "wearable"],
      "Weight and measurement related": ["weight measurement", "measurement issue", "weighing"],
    },
  },
  "Transition Related": {
    keywords: ["transition", "transfer", "new dietitian", "old dietitian", "notice period", "exited"],
    subcategories: {
      "Dietitian has exited or under notice period": ["exited", "notice period", "dietitian left"],
      "Follow up missed by new dietitian": ["new dietitian follow up", "new dietitian missed"],
      "Follow up missed by old dietitian": ["old dietitian follow up", "old dietitian missed"],
      "Motivation Gap": ["motivation gap", "no motivation", "demotivated"],
      "Wrong assignment of dietitian": ["wrong assignment transition", "wrong dietitian transition"],
    },
  },
  "Weight Stuck / Slow Progress Related": {
    keywords: ["weight stuck", "no progress", "slow progress", "plateau", "not losing"],
    subcategories: {
      "Challenges at clients end": ["client challenge", "client end issue", "client side problem"],
      "Challenges at dietitians end": ["dietitian challenge", "dietitian end issue", "dietitian side problem"],
    },
  },
  "Wellness Related": {
    keywords: ["wellness", "mind coach", "live session", "wellness coach", "counselling discrepancy"],
    subcategories: {
      "Counselling discrepancy by the client": ["discrepancy client", "client discrepancy counselling"],
      "Counselling missed by the coach": ["coach missed", "wellness coach missed", "mind coach missed"],
      "Delay in plan publish": ["wellness delay", "plan delay wellness"],
      "Live session related issues": ["live session", "online session", "session issue"],
      "Mind Coach-related issues": ["mind coach", "mental coach", "mind coach issue"],
      "Wellness Coach not assigned": ["wellness coach not assigned", "no wellness coach", "coach not assigned"],
    },
  },
};

const mainCategoryOptions = Object.keys(categoryTree).map((label) => ({
  label: __(label),
  value: label,
}));

const dispositionTypeOptions = [
  { label: __("Resolved"), value: "Resolved" },
  { label: __("Unresolved"), value: "Unresolved" },
  { label: __("Follow Up Required"), value: "Follow Up Required" },
];

const dispositionForm = reactive({
  client_name: "",
  client_code: "",
  remarks: "",
  category: "",
  sub_category: "",
  disposition_type: "",
});

const subCategoryOptions = computed(() => {
  const subCategories = categoryTree[dispositionForm.category]?.subcategories || {};
  return Object.keys(subCategories).map((label) => ({
    label: __(label),
    value: label,
  }));
});

function detectCategories(text: string) {
  const lower = (text || "").toLowerCase();
  let bestMain = "";
  let bestMainScore = 0;
  let bestSub = "";
  let bestSubScore = 0;

  for (const [main, data] of Object.entries(categoryTree)) {
    let mainScore = 0;
    for (const kw of data.keywords) {
      if (lower.includes(kw)) mainScore++;
    }

    if (mainScore > bestMainScore) {
      bestMainScore = mainScore;
      bestMain = main;
      bestSub = "";
      bestSubScore = 0;

      for (const [sub, subKws] of Object.entries(data.subcategories)) {
        let subScore = 0;
        for (const kw of subKws) {
          if (lower.includes(kw)) subScore++;
        }
        if (subScore > bestSubScore) {
          bestSubScore = subScore;
          bestSub = sub;
        }
      }
    }
  }

  return {
    main: bestMainScore > 0 ? bestMain : "",
    sub: bestSubScore > 0 ? bestSub : "",
  };
}

watch(
  () => dispositionForm.remarks,
  (text) => {
    const detected = detectCategories(String(text || ""));

    if (detected.main) {
      dispositionForm.category = detected.main;
      isAutoDetectedCategory.value = true;
    } else {
      isAutoDetectedCategory.value = false;
    }

    if (detected.sub) {
      dispositionForm.sub_category = detected.sub;
      isAutoDetectedSubCategory.value = true;
    } else {
      isAutoDetectedSubCategory.value = false;
    }
  }
);

watch(
  () => dispositionForm.category,
  () => {
    const allowed = Object.keys(
      categoryTree[dispositionForm.category]?.subcategories || {}
    );
    if (!allowed.includes(dispositionForm.sub_category)) {
      dispositionForm.sub_category = "";
      isAutoDetectedSubCategory.value = false;
    }
  }
);

function onManualMainCategoryChange() {
  isAutoDetectedCategory.value = false;
  isAutoDetectedSubCategory.value = false;
  dispositionForm.sub_category = "";
}

function onManualSubCategoryChange() {
  isAutoDetectedSubCategory.value = false;
}

function extractClientDetailsFromBody(body: string) {
  const sourceText = String(body || "");
  const clientNameMatch = sourceText.match(/Customer Name[:\s]+([^\n<]+)/i);
  const clientCodeMatch = sourceText.match(/Customer Code[:\s]+([^\n<]+)/i);

  return {
    clientName: clientNameMatch?.[1]?.trim() || "",
    clientCode: clientCodeMatch?.[1]?.trim() || "",
  };
}

function getTicketBodyText(source: Record<string, any>) {
  return (
    source.description ||
    source.content ||
    source.summary ||
    source.resolution_details ||
    ""
  );
}

function openCloseDispositionModal() {
  const source = ticket.value?.doc || {};
  const bodyText = getTicketBodyText(source);
  const { clientName, clientCode } = extractClientDetailsFromBody(bodyText);

  dispositionForm.client_name = clientName || source.custom_client_name || "";
  dispositionForm.client_code = clientCode || source.custom_client_code || "";
  dispositionForm.remarks = source.custom_remarks || "";
  dispositionForm.category = source.custom_category || "";
  dispositionForm.sub_category = source.custom_sub_category || "";
  dispositionForm.disposition_type = source.custom_disposition_type || "";
  isAutoDetectedCategory.value = false;
  isAutoDetectedSubCategory.value = false;
  showCloseDispositionModal.value = true;
}

async function submitDispositionAndClose() {
  if (!ticket.value?.setValue?.submit || isSubmittingDisposition.value) return;

  if (!String(dispositionForm.remarks || "").trim() || !dispositionForm.disposition_type) {
    toast.error(__("Please fill Remarks and Disposition Type."));
    return;
  }

  const payload = {
    status: "Resolved",
    custom_client_name: dispositionForm.client_name,
    custom_client_code: dispositionForm.client_code,
    custom_remarks: dispositionForm.remarks,
    custom_category: dispositionForm.category,
    custom_sub_category: dispositionForm.sub_category,
    custom_disposition_type: dispositionForm.disposition_type,
  };

  isSubmittingDisposition.value = true;
  notifyTicketUpdate("Status", "Resolved");

  ticket.value.setValue.submit(payload, {
    onSuccess() {
      showCloseDispositionModal.value = false;
      activities.value?.reload?.();
      ticket.value?.reload?.();
      toast.success(__("Ticket closed as Resolved"));
    },
    onError() {
      toast.error(__("Failed to save disposition and close ticket"));
    },
    onFinally() {
      isSubmittingDisposition.value = false;
    },
  });
}

function isCloseTicketAction(action) {
  return (action?.label || "").toLowerCase().trim() === "close ticket";
}

function isDeprecatedPresenceAction(action) {
  const label = String(action?.label || "").toLowerCase().trim();
  return label.includes("go live") || label.includes("offline");
}

function wrapCloseAction(action) {
  if (!action || isDeprecatedPresenceAction(action)) return null;
  const wrapped = { ...action };

  if (Array.isArray(wrapped.items)) {
    wrapped.items = wrapped.items
      .map((item) => wrapCloseAction(item))
      .filter(Boolean);
  }

  if (isCloseTicketAction(wrapped)) {
    wrapped.onClick = () => openCloseDispositionModal();
  }

  return wrapped;
}

const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);
const breadcrumbs = computed(() => {

  let items = [{ label: __("Tickets"), route: { name: "TicketsAgent" } }];
  if (route.query.view) {
    const currView: ComputedRef<View> = findView(route.query.view as string);
    if (currView) {
      items.push({
        label: currView.value?.label,
        icon: getIcon(currView.value?.icon),
        route: { name: "TicketsAgent", query: { view: currView.value?.name } },
      });
    }
  }
  items.push({
    label: ticket.value.doc?.subject,
    onClick: () => {
      showSubjectDialog.value = true;
    },
  });
  return items;
});

function updateField(fieldname: string, value: string, callback = () => {}) {
  const doc = ticket.value;
  doc.setValue.submit({
    [fieldname]: value,
  });
  callback();
}

const showMergeModal = ref(false);
const showMergeOption = computed(() => {
  return (
    !ticket.value.doc.is_merged &&
    ["Open", "Paused"].includes(ticket.value.doc.status_category)
  );
});
const defaultActions = computed(() => {
  let items = [];

  if (showMergeOption.value) {
    items.push({
      label: __("Merge Ticket"),
      icon: LucideMerge,
      condition: () => !ticket.value.doc.is_merged,
      onClick: () => (showMergeModal.value = true),
    });
  }
  return [
    {
      group: __("Default actions"),
      hideLabel: true,
      items,
    },
  ];
});
const actions = ref([]);
const normalActions = computed(() => {
  return actions.value.filter((action) => !action.group);
});

const groupedWithLabelActions = computed(() => {
  let _actions = [];

  actions.value
    .filter((action) => action.buttonLabel && action.group)
    .forEach((action) => {
      let groupIndex = _actions.findIndex(
        (a) => a.label === action.buttonLabel
      );
      if (groupIndex > -1) {
        _actions[groupIndex].action.push(action);
      } else {
        _actions.push({
          label: action.buttonLabel,
          action: [action],
        });
      }
    });
  return _actions;
});

const groupedActions = computed(() => {
  let _actions = [];
  _actions = _actions.concat(
    actions.value.filter((action) => action.group && !action.buttonLabel)
  );
  return _actions;
});

const customizationCtx = computed(() => ({
  doc: ticket?.value?.doc,
  call,
  router,
  toast,
  $dialog: globalStore().$dialog,
  updateField,
  createToast: toast.create,
}));

watchEffect(async () => {
  if (customizations.value?.data) {
    await setupCustomizations(
      customizations.value.data,
      customizationCtx.value
    );

    const customActions = (customizations.value?.data?._customActions || []).map((action) => wrapCloseAction(action)).filter(Boolean);
    actions.value = [
      ...defaultActions.value,
      ...customActions,
    ];
  }
});

</script>

<style>
.breadcrumbs button {
  background-color: inherit !important;
  &:hover,
  &:focus {
    background-color: inherit !important;
  }
}
</style>
