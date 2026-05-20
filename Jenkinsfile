
pipeline {
    agent {
        label 'documentation'
    }
    environment {
        ANTORA_VERSION = 'antora/antora:3.1.9'
    }
    stages {

        stage('Community Documentation Preview') {
            steps {
                script {
                    // Ensure Docker is running
                    sh "sudo systemctl start docker || true"
                    // Run Antora for community-local-playbook.yml
                    sh """
                    sudo docker run --entrypoint antora -v ${WORKSPACE}:/antora -u 1000 --rm -t ${env.ANTORA_VERSION} generate --stacktrace community-local-playbook.yml
                    """
                }
            }
        }

        stage('Enterprise Documentation Preview') {
            steps {
                script {
                    // Ensure Docker is running
                    sh "sudo systemctl start docker || true"
                    // Run Antora for enterprise-local-playbook.yml
                    sh """
                    sudo docker run --entrypoint antora -v ${WORKSPACE}:/antora -u 1000 --rm -t ${env.ANTORA_VERSION} generate --stacktrace enterprise-local-playbook.yml
                    """
                }
            }
        }

        stage('Archive and Publish Generated Docs') {
            steps {
                // Archive community and enterprise docs as Jenkins artifacts
                archiveArtifacts artifacts: 'build/community/html/**', allowEmptyArchive: true
                archiveArtifacts artifacts: 'build/enterprise/html/**', allowEmptyArchive: true

                // Publish HTML reports
                publishHTML([
                    reportName: 'Community Documentation',
                    reportDir: 'build/community/html',
                    reportFiles: 'index.html',
                    keepAll: true,
                    alwaysLinkToLastBuild: true,
                    allowMissing: false
                ])

                publishHTML([
                    reportName: 'Enterprise Documentation',
                    reportDir: 'build/enterprise/html',
                    reportFiles: 'index.html',
                    keepAll: true,
                    alwaysLinkToLastBuild: true,
                    allowMissing: false
                ])
            }
        }
    }

    post {
        success {
            echo 'Documentation previews generated and archived successfully.'
            script {
                def prNumber = env.CHANGE_ID ?: env.ghprbPullId
                if (prNumber) {
                    def baseUrl = "https://jenkins.payara.fish/view/Documentation/job/Documentation/job/Payara-Documentation%20PR%20Deploy%20Preview/view/change-requests/job/PR-${prNumber}"
                    def communityUrl = "${baseUrl}/Community_20Documentation/"
                    def enterpriseUrl = "${baseUrl}/Enterprise_20Documentation/"
                    def commentMarker = "<!-- jenkins-doc-preview -->"
                    def commentBody = "${commentMarker}\\n" +
                        "##  Documentation Preview\\n\\n" +
                        "> Preview links are updated automatically on every commit push.\\n\\n" +
                        "| Variant | Preview Link |\\n" +
                        "|---|---|\\n" +
                        "|  **Community** | [:arrow_upper_right: Open Community Docs](${communityUrl}) |\\n" +
                        "|  **Enterprise** | [:arrow_upper_right: Open Enterprise Docs](${enterpriseUrl}) |\\n\\n" +
                        "---\\n" +
                        " *Updated by Jenkins build [#${env.BUILD_NUMBER}](${env.BUILD_URL})*"
                    withCredentials([usernamePassword(credentialsId: 'payara-devops-github-personal-access-token-as-username-password',
                                                     passwordVariable: 'GITHUB_TOKEN',
                                                     usernameVariable: 'GITHUB_USER')]) {
                        sh """
                        # Delete existing preview comment if present
                        COMMENT_ID=\$(curl -s \\
                          -H "Authorization: token \${GITHUB_TOKEN}" \\
                          "https://api.github.com/repos/payara/Payara-Documentation/issues/${prNumber}/comments?per_page=100" | \\
                          python3 -c "import sys,json; comments=json.load(sys.stdin); ids=[str(c['id']) for c in comments if '<!-- jenkins-doc-preview -->' in c.get('body','')]; print(ids[0] if ids else '')")
                        if [ -n "\$COMMENT_ID" ]; then
                          curl -s -X DELETE \\
                            -H "Authorization: token \${GITHUB_TOKEN}" \\
                            "https://api.github.com/repos/payara/Payara-Documentation/issues/comments/\${COMMENT_ID}"
                        fi

                        # Post fresh preview comment
                        curl -s -X POST \\
                          -H "Authorization: token \${GITHUB_TOKEN}" \\
                          -H "Content-Type: application/json" \\
                          -d '{"body":"${commentBody}"}' \\
                          "https://api.github.com/repos/payara/Payara-Documentation/issues/${prNumber}/comments"
                        """
                    }
                }
            }
        }
        failure {
            echo 'Failed to generate documentation previews.'
        }
    }
}
