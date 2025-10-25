# FAQ - Système de Rooms de Quiz

## 🎯 Questions Générales

### Q: Qu'est-ce qu'une Room?
**R:** Une Room est une session de quiz créée par un enseignant. Elle permet aux étudiants de rejoindre avec un code et de passer le quiz en même temps.

### Q: Comment fonctionne le code de partage?
**R:** Chaque room reçoit un code unique de 6 caractères (ex: ABC123). L'enseignant partage ce code avec les étudiants, qui l'utilisent pour rejoindre la room.

### Q: Combien d'étudiants peuvent rejoindre une room?
**R:** Par défaut, il n'y a pas de limite, mais vous pouvez configurer un nombre maximum de participants lors de la création.

### Q: Que se passe-t-il si un étudiant rejoint après le démarrage?
**R:** L'étudiant ne peut pas rejoindre une room qui a déjà commencé. Il doit rejoindre avant le démarrage.

## 👨‍🏫 Questions pour les Enseignants

### Q: Comment créer une room?
**R:** 
1. Allez à `/gamification/teacher/rooms/`
2. Cliquez sur "Créer une Room"
3. Remplissez le formulaire
4. Cliquez sur "Créer"

### Q: Puis-je créer une room avec un quiz existant?
**R:** Oui, sélectionnez simplement le quiz dans le formulaire de création.

### Q: Puis-je créer une room avec un quiz généré par IA?
**R:** Oui, cliquez sur "Créer avec IA" et spécifiez le sujet, la difficulté et le nombre de questions.

### Q: Comment démarrer une room?
**R:** 
1. Allez à la page de détails de la room
2. Cliquez sur "Démarrer la Room"
3. Les étudiants peuvent maintenant commencer le quiz

### Q: Comment terminer une room?
**R:** 
1. Allez à la page de détails de la room
2. Cliquez sur "Terminer la Room"
3. Les résultats sont finalisés

### Q: Puis-je modifier une room après sa création?
**R:** Non, vous ne pouvez pas modifier une room après sa création. Vous devez la supprimer et en créer une nouvelle.

### Q: Puis-je supprimer une room?
**R:** Oui, cliquez sur "Supprimer" sur la page de détails. Attention: cela supprimera aussi tous les résultats.

### Q: Comment voir les résultats?
**R:** Allez à la page de détails de la room. Vous verrez une liste de tous les participants et leurs résultats.

### Q: Puis-je exporter les résultats?
**R:** Actuellement, vous pouvez voir les résultats dans le tableau de bord. L'export sera disponible dans une version future.

## 👨‍🎓 Questions pour les Étudiants

### Q: Comment rejoindre une room?
**R:**
1. Allez à `/gamification/student/room/join/`
2. Entrez le code fourni par l'enseignant
3. Cliquez sur "Rejoindre"

### Q: Que se passe-t-il si j'entre un mauvais code?
**R:** Vous verrez un message d'erreur. Vérifiez le code et réessayez.

### Q: Puis-je rejoindre plusieurs rooms?
**R:** Oui, vous pouvez rejoindre autant de rooms que vous voulez.

### Q: Que se passe-t-il si je quitte le quiz avant de le terminer?
**R:** Vos réponses ne seront pas sauvegardées. Vous devrez recommencer.

### Q: Puis-je modifier mes réponses après les avoir soumises?
**R:** Non, une fois soumises, vos réponses ne peuvent pas être modifiées.

### Q: Puis-je voir mes réponses après le quiz?
**R:** Oui, si l'enseignant a activé l'option "Permettre la révision des réponses".

### Q: Comment fonctionne le timer?
**R:** Le timer compte à rebours depuis le début du quiz. Quand le temps est écoulé, le quiz est automatiquement soumis.

### Q: Que se passe-t-il si le temps s'écoule?
**R:** Le quiz est automatiquement soumis avec les réponses que vous avez données jusqu'à présent.

### Q: Comment voir mon classement?
**R:** Allez à la page "Classement" de la room. Vous verrez votre position et vos statistiques.

### Q: Comment gagner des badges?
**R:** Les badges sont attribués automatiquement selon vos performances (score, rapidité, précision, etc.).

## 📊 Questions sur les Résultats

### Q: Comment est calculé mon score?
**R:** Votre score est basé sur le nombre de réponses correctes. Chaque réponse correcte vaut des points.

### Q: Comment est calculé mon grade?
**R:** Votre grade est basé sur votre pourcentage:
- A+: 90-100%
- A: 80-89%
- B: 70-79%
- C: 60-69%
- D: 50-59%
- F: <50%

### Q: Qu'est-ce que le classement?
**R:** Le classement montre votre position par rapport aux autres participants de la room, basé sur votre pourcentage.

### Q: Qu'est-ce que les badges?
**R:** Les badges sont des récompenses attribuées pour différentes performances (score élevé, rapidité, précision, etc.).

### Q: Comment puis-je améliorer mon score?
**R:** Pratiquez davantage, révisez le matériel et essayez de répondre plus rapidement et précisément.

## 🔧 Questions Techniques

### Q: Quels navigateurs sont supportés?
**R:** Tous les navigateurs modernes (Chrome, Firefox, Safari, Edge).

### Q: Puis-je utiliser mon téléphone?
**R:** Oui, le système est responsive et fonctionne sur les téléphones.

### Q: Que se passe-t-il si je perds ma connexion?
**R:** Vos réponses ne seront pas sauvegardées. Reconnectez-vous et recommencez.

### Q: Combien de temps les données sont-elles conservées?
**R:** Les données sont conservées indéfiniment, sauf si l'enseignant supprime la room.

### Q: Mes données sont-elles sécurisées?
**R:** Oui, toutes les données sont chiffrées et sécurisées. Seuls les utilisateurs autorisés peuvent y accéder.

## 🐛 Dépannage

### Q: Je ne peux pas créer une room
**R:** Vérifiez que:
- Vous êtes connecté en tant qu'enseignant
- Vous avez les permissions nécessaires
- Il y a au moins un quiz disponible

### Q: Je ne peux pas rejoindre une room
**R:** Vérifiez que:
- Le code est correct
- La room existe
- La room n'a pas encore commencé
- Vous n'avez pas déjà rejoint cette room

### Q: Je ne vois pas mes résultats
**R:** Vérifiez que:
- Vous avez soumis le quiz
- La room est terminée
- Vous êtes connecté avec le bon compte

### Q: Le timer ne fonctionne pas
**R:** Essayez:
- Rafraîchir la page
- Vider le cache du navigateur
- Utiliser un autre navigateur

### Q: Je ne vois pas le classement
**R:** Vérifiez que:
- L'enseignant a activé l'option "Afficher le classement"
- Au moins 2 participants ont terminé le quiz

### Q: Les badges ne s'affichent pas
**R:** Vérifiez que:
- L'enseignant a activé l'option "Activer les badges"
- Vous avez atteint les critères pour les badges

## 📞 Support

### Q: Où puis-je obtenir de l'aide?
**R:** Consultez:
1. Ce fichier FAQ
2. Le guide complet (ROOM_SYSTEM_GUIDE.md)
3. Le guide de démarrage rapide (QUICK_START.md)
4. Contactez votre administrateur

### Q: Comment signaler un bug?
**R:** Contactez votre administrateur avec:
- Une description du problème
- Les étapes pour reproduire
- Des captures d'écran si possible

### Q: Comment suggérer une amélioration?
**R:** Contactez votre administrateur avec votre suggestion.

## 🎓 Questions Pédagogiques

### Q: Comment utiliser les rooms pour l'enseignement?
**R:** Vous pouvez utiliser les rooms pour:
- Évaluer les connaissances
- Pratiquer les compétences
- Compétitions amicales
- Révisions

### Q: Comment motiver les étudiants?
**R:** Utilisez:
- Les badges pour récompenser les performances
- Le classement pour créer une saine compétition
- Les résultats pour montrer les progrès

### Q: Comment identifier les étudiants ayant besoin d'aide?
**R:** Consultez:
- Les résultats pour voir les scores faibles
- Les statistiques pour voir les questions problématiques
- Le classement pour voir les positions

### Q: Comment suivre les progrès?
**R:** Comparez:
- Les scores entre les quizzes
- Les grades entre les sessions
- Les badges gagnés au fil du temps

## 🌟 Conseils et Astuces

### Conseil 1: Préparez vos quizzes
Créez vos quizzes à l'avance pour éviter les retards.

### Conseil 2: Testez avant la classe
Testez la room avant de la partager avec les étudiants.

### Conseil 3: Donnez du temps
Donnez aux étudiants suffisamment de temps pour rejoindre avant de démarrer.

### Conseil 4: Utilisez les résultats
Utilisez les résultats pour améliorer votre enseignement.

### Conseil 5: Encouragez la participation
Encouragez les étudiants à participer en utilisant les badges et le classement.

### Conseil 6: Soyez juste
Assurez-vous que tous les étudiants ont les mêmes conditions (temps, questions, etc.).

### Conseil 7: Donnez du feedback
Donnez du feedback aux étudiants sur leurs performances.

### Conseil 8: Célébrez les succès
Célébrez les succès des étudiants pour les motiver.

---

**Dernière mise à jour**: 2025-10-25
**Version**: 1.0

**Besoin d'aide?** Consultez les autres fichiers de documentation ou contactez votre administrateur.

