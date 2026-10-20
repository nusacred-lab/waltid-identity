<template>
    <nav aria-label="Table of contents">
        <ul class="mt-5">
            <TocElement v-for="element in tableOfContents" :key="element.id"
                :toc-element="element" class="table-of-contents-element" />
        </ul>
    </nav>
</template>

<script lang="ts" setup>
import TocElement from "~/components/tableOfContents/TocElement.vue";
import { contentNodes, contentText } from "~/utils/contentNodes";

const route = useRoute();
const { data: page } = await useAsyncData(
    () => `content-toc:${route.path}`,
    () => queryCollection('content').path(route.path).first(),
);
const tableOfContents = computed(() => contentNodes(page.value?.body)
    .filter(node => /^h[1-6]$/.test(node.tag ?? '') && typeof node.props?.id === 'string')
    .map(node => ({ tag: node.tag!, id: String(node.props!.id), value: contentText(node) })));
</script>
