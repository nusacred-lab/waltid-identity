<script setup lang="ts">
const route = useRoute()
const { data: page } = await useAsyncData(
    () => `content:${route.path}`,
    () => queryCollection('content').path(route.path).first(),
)

if (!page.value) {
    throw createError({ statusCode: 404, statusMessage: 'Page not found' })
}

useSeoMeta({
    title: () => page.value?.title,
    description: () => page.value?.description,
})
</script>

<template>
    <main>
        <ContentRenderer v-if="page" :value="page" />
    </main>
</template>
