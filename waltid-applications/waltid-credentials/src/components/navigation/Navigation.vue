<template>
  <nav class="px-5">
    <template v-if="navigation">
      <ul>
        <li
          v-for="link of navigation"
          :key="link.path"
          class="text-gray-50 font-semibold"
        >
          <NuxtLink
            v-if="!link.children?.length"
            :to="link.path"
            class="block my-2 font-normal"
            :class="
              $route.path === link.path
                ? 'text-primary-300 border-primary-300'
                : ''
            "
            @click="(e) => emit('click', e)"
            >{{ link.title }}</NuxtLink
          >
          <span v-if="link.children?.length" class="block my-2">{{ link.title }}</span>
          <ul v-if="link.children?.length" class="text-gray-300 font-normal mt-2">
            <li
              v-for="child of link.children"
              :key="child.path"
              class="border-l border-gray-700 pl-3 py-0.8 ml-0.5"
              :class="
                $route.path === child.path
                  ? 'text-primary-300 border-primary-300'
                  : ''
              "
            >
              <NuxtLink :to="child.path" @click="(e) => emit('click', e)">{{
                child.title
              }}</NuxtLink>
            </li>
          </ul>
        </li>
      </ul>
    </template>
  </nav>
</template>

<script setup lang="ts">
const { data: navigation } = await useAsyncData('content-navigation', () => queryCollectionNavigation('content'));

const emit = defineEmits<{ (event: "click", e: Event): void }>();
</script>
