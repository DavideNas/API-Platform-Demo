pipeline {
    agent any

    environment {
        REGISTRY        = "registry.devplatform.local"
        IMAGE_NAME       = "api-platform-demo"
        IMAGE_TAG        = "${env.BUILD_NUMBER}"
        FULL_IMAGE       = "${REGISTRY}:80/${IMAGE_NAME}:${IMAGE_TAG}"
        KUBE_NAMESPACE   = "api-platform"
    }

    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Unit Test') {
            steps {
                dir('app') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        python3 -m pytest -v --junitxml=test-results.xml
                    '''
                }
            }
           post {
                always {
                    junit 'app/test-results.xml'
                }
            }
        }

        stage('Build Image') {
            steps {
                dir('app') {
                    sh "docker build -t ${FULL_IMAGE} --build-arg APP_VERSION=${IMAGE_TAG} ."
                }
            }
        }

        stage('Scan Image') {
            steps {
                sh """
                    echo "Eseguo scan di sicurezza sull'immagine ${FULL_IMAGE}..."
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy:latest image --exit-code 0 --severity HIGH,CRITICAL ${FULL_IMAGE} || true
                """
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'registry-creds', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
                    sh """
                        echo "\$REG_PASS" | docker login ${REGISTRY}:80 -u "\$REG_USER" --password-stdin
                        docker push ${FULL_IMAGE}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-devplatform', variable: 'KUBECONFIG_FILE')]) {
                    // Usiamo i doppi apici per interpolare ${KUBE_NAMESPACE} e ${FULL_IMAGE}, 
                    // e mettiamo il backslash davanti a \$KUBECONFIG_FILE per farlo leggere a Bash e non a Jenkins.
                    sh """
                        export KUBECONFIG=\$KUBECONFIG_FILE
                        kubectl -n ${KUBE_NAMESPACE} set image deployment/api-platform-demo api-platform-demo=${FULL_IMAGE}
                        kubectl -n ${KUBE_NAMESPACE} rollout status deployment/api-platform-demo --timeout=120s
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completata con successo. Immagine deployata: ${FULL_IMAGE}"
        }
        failure {
            echo "Pipeline fallita. Verifico se serve un rollback manuale con: kubectl rollout undo deployment/api-platform-demo -n ${KUBE_NAMESPACE}"
        }
    }
}
