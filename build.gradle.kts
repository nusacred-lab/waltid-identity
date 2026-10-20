import com.github.benmanes.gradle.versions.updates.DependencyUpdatesTask

plugins {
    alias(identityLibs.plugins.android.application) apply false
    alias(identityLibs.plugins.kotlin.multiplatform) apply false
    alias(identityLibs.plugins.kotlin.compose) apply false
    alias(identityLibs.plugins.compose.multiplatform) apply false
    alias(identityLibs.plugins.kotlin.serialization) apply false
    alias(identityLibs.plugins.buildconfig) apply false
    alias(identityLibs.plugins.sqldelight) apply false
    id("waltid.licensereport") apply false
    alias(identityLibs.plugins.google.services) apply false
}

// License reporting resolves every runtime classpath and downloads every POM in the parent
// chain, so it is opt-in rather than always on:
// ./gradlew -p waltid-identity -PenableLicenseReport=true aggregateDependencyNotices --no-configuration-cache
if (providers.gradleProperty("enableLicenseReport").orNull.toBoolean()) {
    apply(plugin = "waltid.licensereport")

    subprojects {
        if (subprojects.isEmpty()) {
            apply(plugin = "waltid.licensereport")
        }
    }
}

// Report stable updates while preserving dependencies intentionally on preview tracks.
tasks.withType<DependencyUpdatesTask>().configureEach {
    checkConstraints = true
    // Cinterop commonization resolves derived artifacts, not dependency update candidates.
    filterConfigurations = Spec {
        it.attributes.getAttribute(Usage.USAGE_ATTRIBUTE)?.name != "kotlin-commonized-cinterop"
    }
    rejectPreReleases = true
}

// Source-build all direct and transitive COSE references; never fall back to the opaque snapshot.
subprojects {
    configurations.configureEach {
        resolutionStrategy.dependencySubstitution {
            substitute(module("org.cose:cose-java")).using(project(":third-party:cose-java"))
        }
    }
}

tasks.register("verifyCoseReplacement") {
    group = "verification"
    description = "Check every API2 runtime uses the source project and no external COSE/LTS binary."
    doLast {
        listOf("issuer", "wallet", "verifier").forEach { service ->
            val target = project(":waltid-services:waltid-$service-api2")
            val components = target.configurations.getByName("runtimeClasspath")
                .incoming.resolutionResult.allComponents.map { it.id }
            val external = components.filterIsInstance<org.gradle.api.artifacts.component.ModuleComponentIdentifier>()
            check(external.none { it.group == "org.cose" && it.module == "cose-java" }) {
                "$service still resolves an external COSE binary"
            }
            check(components.filterIsInstance<org.gradle.api.artifacts.component.ProjectComponentIdentifier>()
                .any { it.projectPath == ":third-party:cose-java" }) {
                "$service does not resolve the source-built COSE project"
            }
            check(external.none { it.group == "org.bouncycastle" && it.module.endsWith("lts8on") }) {
                "$service resolves duplicate BouncyCastle LTS classes"
            }
            println("COSE_SOURCE_PROJECT_VERIFIED: $service")
        }
    }
}

// Export the actual three runtime graphs, not the union of test/platform lock entries.
tasks.register("collectBaselineRuntimeEvidence") {
    group = "verification"
    dependsOn(listOf("issuer", "wallet", "verifier").map { ":waltid-services:waltid-$it-api2:buildFatJar" })
    doLast {
        fun digest(file: File): String {
            val md = java.security.MessageDigest.getInstance("SHA-256")
            file.inputStream().use { input ->
                val buffer = ByteArray(65536)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    md.update(buffer, 0, count)
                }
            }
            return md.digest().joinToString("") { "%02x".format(it) }
        }
        val output = layout.buildDirectory.dir("baseline-evidence").get().asFile
        output.deleteRecursively()
        output.mkdirs()
        listOf("issuer", "wallet", "verifier").forEach { service ->
            val target = project(":waltid-services:waltid-$service-api2")
            val runtimeDir = output.resolve("runtime/$service").apply { mkdirs() }
            val artifacts = target.configurations.getByName("runtimeClasspath").incoming.artifacts.artifacts
                .sortedBy { it.id.displayName }.map { artifact ->
                    val hash = digest(artifact.file)
                    artifact.file.copyTo(runtimeDir.resolve("$hash-${artifact.file.name}"), overwrite = true)
                    mapOf("component" to artifact.id.componentIdentifier.displayName,
                        "file" to artifact.file.name, "sha256" to hash)
                }
            val fatJars = target.tasks.named("buildFatJar").get().outputs.files.files
                .filter { it.isFile && it.extension == "jar" }.map { file ->
                    val destination = output.resolve("fat-jars/$service.jar")
                    destination.parentFile.mkdirs()
                    file.copyTo(destination, overwrite = true)
                    mapOf("file" to "$service.jar", "sha256" to digest(file))
                }
            check(fatJars.size == 1) { "Expected exactly one $service fat JAR" }
            val manifest = mapOf("service" to service,
                "workflowSourceSha" to providers.environmentVariable("GITHUB_SHA").orNull,
                "runtimeArtifacts" to artifacts, "fatJars" to fatJars)
            output.resolve("$service-runtime.json").writeText(
                groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(manifest)) + "\n")
            println("BASELINE_RUNTIME_EXPORTED: $service (${artifacts.size} artifacts)")
        }
    }
}
