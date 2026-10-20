import { queryCollection } from "@nuxt/content/server";
import { contentNodes } from "~/utils/contentNodes";

export default defineEventHandler(async (event) => {
    const contentQuery = await queryCollection(event, "content").all();
    return contentQuery.filter((page) => page.path?.startsWith("/w3c-credentials/") && contentNodes(page.body).find((elem) => elem.tag === "pre" && elem.props?.language === "json") != undefined).map((elem) => elem.title);
});
