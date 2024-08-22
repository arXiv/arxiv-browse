-- SET FOREIGN_KEY_CHECKS = 0;
-- PRAGMA foreign_keys = OFF; -- for newer versions of sqlite3

-- 0704.0361
INSERT INTO `arXiv_dblp` VALUES (422353,'db/journals/corr/corr0704.html#abs-0704-0361');
INSERT INTO `arXiv_dblp_authors` VALUES (10912,'Ioannis Chatzigeorgiou'),(10913,'Miguel R. D. Rodrigues'),(10914,'Ian J. Wassell'),(10915,'Rolando A. Carrasco');
INSERT INTO `arXiv_dblp_document_authors` (`document_id`, `author_id`, `position`) VALUES (422353,10912,1),(422353,10913,2),(422353,10914,3),(422353,10915,4);

-- cs/0006008
INSERT INTO `arXiv_dblp` VALUES (233,'db/journals/corr/corr0006.html#cs-DC-0006008');
INSERT INTO `arXiv_dblp_authors` VALUES (1575,'Joseph Y. Halpern'),(5488,'Cynthia Dwork'),(5490,'Orli Waarts');
INSERT INTO `arXiv_dblp_document_authors` VALUES (233,1575,2),(233,5488,1),(233,5490,3);
