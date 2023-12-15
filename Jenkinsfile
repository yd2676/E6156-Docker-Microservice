pipeline {
  agent any

  stages {
    stage('Build') {
      steps {
        sh 'docker build -t ds .'
        sh 'docker tag ds $DOCKER_IMAGE'
      }
    }
    stage('Test') {
      steps {
        sh 'docker run ds python -m pytest /code/tests/'
      }
    }
    stage('Deploy') {
      steps {
        withCredentials([usernamePassword(credentialsId: "${DOCKER_REGISTRY_CREDS}", passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
          sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin docker.io"
          sh 'docker push $DOCKER_IMAGE'
        }
      }
    }
  }
  post {
    always {
      sh 'docker logout'
    }
  }
}
