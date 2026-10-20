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
