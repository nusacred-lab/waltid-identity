plugins { `java-library` }

group = "dev.nusacred.thirdparty"
version = "1.1.1-fc897fa9-nusacred.1"

repositories { mavenCentral() }

java {
    toolchain { languageVersion.set(JavaLanguageVersion.of(21)) }
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
    withSourcesJar()
}

tasks.withType<JavaCompile>().configureEach {
    options.release.set(17)
    options.encoding = "UTF-8"
}

dependencies {
    api(identityLibs.cose.cbor)
    implementation(identityLibs.bouncycastle.prov)
    implementation(identityLibs.bouncycastle.pkix)
    implementation("org.slf4j:slf4j-api:${identityLibs.versions.slf4j.simple.get()}")
    compileOnly(identityLibs.cose.lombok)
    annotationProcessor(identityLibs.cose.lombok)
    testImplementation(identityLibs.junit.jupiter.api)
    testImplementation(identityLibs.junit.jupiter.params)
    testRuntimeOnly(identityLibs.junit.jupiter.engine)
    testRuntimeOnly(identityLibs.junit.platform.launcher)
}

dependencyLocking { lockAllConfigurations() }

tasks.withType<Jar>().configureEach {
    archiveBaseName.set("nusacred-cose-java")
    isPreserveFileTimestamps = false
    isReproducibleFileOrder = true
    from("LICENSE") { into("META-INF/licenses/cose-java") }
    from("upstream-source.json") { into("META-INF/nusacred/cose-java") }
    manifest.attributes(
        "Implementation-Title" to "nusacred source-built COSE-JAVA",
        "Implementation-Version" to project.version,
        "Source-Revision" to "fc897fa9da31f35c5f2e3e092496ad1c57e10457",
    )
}

tasks.test {
    useJUnitPlatform()
    enableAssertions = true
    testLogging { showStandardStreams = false }
}
