-- phpMyAdmin SQL Dump
-- version 4.7.4
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 04, 2018 at 11:35 AM
-- Server version: 10.1.28-MariaDB
-- PHP Version: 7.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fusion`
--

-- --------------------------------------------------------

--
-- Table structure for table `academic_information_student`
--

CREATE TABLE `academic_information_student` (
  `id_id` varchar(20) NOT NULL,
  `programme` varchar(10) NOT NULL,
  `cpi` double NOT NULL,
  `category` varchar(10) NOT NULL,
  `father_name` varchar(40) NOT NULL,
  `mother_name` varchar(40) NOT NULL,
  `hall_no` int(11) NOT NULL,
  `room_no` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `academic_information_student`
--

INSERT INTO `academic_information_student` (`id_id`, `programme`, `cpi`, `category`, `father_name`, `mother_name`, `hall_no`, `room_no`) VALUES
('2015335', 'B.Tech', 7, 'GEN', 'Segu Krishna murthy', 'Segu Lakshmi Devi', 3, 'I-206');

-- --------------------------------------------------------

--
-- Table structure for table `account_emailaddress`
--

CREATE TABLE `account_emailaddress` (
  `id` int(11) NOT NULL,
  `email` varchar(254) NOT NULL,
  `verified` tinyint(1) NOT NULL,
  `primary` tinyint(1) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `account_emailconfirmation`
--

CREATE TABLE `account_emailconfirmation` (
  `id` int(11) NOT NULL,
  `created` datetime(6) NOT NULL,
  `sent` datetime(6) DEFAULT NULL,
  `key` varchar(64) NOT NULL,
  `email_address_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(80) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can add permission', 2, 'add_permission'),
(5, 'Can change permission', 2, 'change_permission'),
(6, 'Can delete permission', 2, 'delete_permission'),
(7, 'Can add group', 3, 'add_group'),
(8, 'Can change group', 3, 'change_group'),
(9, 'Can delete group', 3, 'delete_group'),
(10, 'Can add user', 4, 'add_user'),
(11, 'Can change user', 4, 'change_user'),
(12, 'Can delete user', 4, 'delete_user'),
(13, 'Can add content type', 5, 'add_contenttype'),
(14, 'Can change content type', 5, 'change_contenttype'),
(15, 'Can delete content type', 5, 'delete_contenttype'),
(16, 'Can add session', 6, 'add_session'),
(17, 'Can change session', 6, 'change_session'),
(18, 'Can delete session', 6, 'delete_session'),
(19, 'Can add site', 7, 'add_site'),
(20, 'Can change site', 7, 'change_site'),
(21, 'Can delete site', 7, 'delete_site'),
(22, 'Can add register', 8, 'add_register'),
(23, 'Can change register', 8, 'change_register'),
(24, 'Can delete register', 8, 'delete_register'),
(25, 'Can add thesis', 9, 'add_thesis'),
(26, 'Can change thesis', 9, 'change_thesis'),
(27, 'Can delete thesis', 9, 'delete_thesis'),
(28, 'Can add final registrations', 10, 'add_finalregistrations'),
(29, 'Can change final registrations', 10, 'change_finalregistrations'),
(30, 'Can delete final registrations', 10, 'delete_finalregistrations'),
(31, 'Can add calendar', 11, 'add_calendar'),
(32, 'Can change calendar', 11, 'change_calendar'),
(33, 'Can delete calendar', 11, 'delete_calendar'),
(34, 'Can add course', 12, 'add_course'),
(35, 'Can change course', 12, 'change_course'),
(36, 'Can delete course', 12, 'delete_course'),
(37, 'Can add exam_timetable', 13, 'add_exam_timetable'),
(38, 'Can change exam_timetable', 13, 'change_exam_timetable'),
(39, 'Can delete exam_timetable', 13, 'delete_exam_timetable'),
(40, 'Can add grades', 14, 'add_grades'),
(41, 'Can change grades', 14, 'change_grades'),
(42, 'Can delete grades', 14, 'delete_grades'),
(43, 'Can add holiday', 15, 'add_holiday'),
(44, 'Can change holiday', 15, 'change_holiday'),
(45, 'Can delete holiday', 15, 'delete_holiday'),
(46, 'Can add instructor', 16, 'add_instructor'),
(47, 'Can change instructor', 16, 'change_instructor'),
(48, 'Can delete instructor', 16, 'delete_instructor'),
(49, 'Can add meeting', 17, 'add_meeting'),
(50, 'Can change meeting', 17, 'change_meeting'),
(51, 'Can delete meeting', 17, 'delete_meeting'),
(52, 'Can add spi', 18, 'add_spi'),
(53, 'Can change spi', 18, 'change_spi'),
(54, 'Can delete spi', 18, 'delete_spi'),
(55, 'Can add student', 19, 'add_student'),
(56, 'Can change student', 19, 'change_student'),
(57, 'Can delete student', 19, 'delete_student'),
(58, 'Can add student_attendance', 20, 'add_student_attendance'),
(59, 'Can change student_attendance', 20, 'change_student_attendance'),
(60, 'Can delete student_attendance', 20, 'delete_student_attendance'),
(61, 'Can add timetable', 21, 'add_timetable'),
(62, 'Can change timetable', 21, 'change_timetable'),
(63, 'Can delete timetable', 21, 'delete_timetable'),
(64, 'Can add mess', 22, 'add_mess'),
(65, 'Can change mess', 22, 'change_mess'),
(66, 'Can delete mess', 22, 'delete_mess'),
(67, 'Can add monthly_bill', 23, 'add_monthly_bill'),
(68, 'Can change monthly_bill', 23, 'change_monthly_bill'),
(69, 'Can delete monthly_bill', 23, 'delete_monthly_bill'),
(70, 'Can add payments', 24, 'add_payments'),
(71, 'Can change payments', 24, 'change_payments'),
(72, 'Can delete payments', 24, 'delete_payments'),
(73, 'Can add menu', 25, 'add_menu'),
(74, 'Can change menu', 25, 'change_menu'),
(75, 'Can delete menu', 25, 'delete_menu'),
(76, 'Can add rebate', 26, 'add_rebate'),
(77, 'Can change rebate', 26, 'change_rebate'),
(78, 'Can delete rebate', 26, 'delete_rebate'),
(79, 'Can add vacation_food', 27, 'add_vacation_food'),
(80, 'Can change vacation_food', 27, 'change_vacation_food'),
(81, 'Can delete vacation_food', 27, 'delete_vacation_food'),
(82, 'Can add nonveg_menu', 28, 'add_nonveg_menu'),
(83, 'Can change nonveg_menu', 28, 'change_nonveg_menu'),
(84, 'Can delete nonveg_menu', 28, 'delete_nonveg_menu'),
(85, 'Can add nonveg_data', 29, 'add_nonveg_data'),
(86, 'Can change nonveg_data', 29, 'change_nonveg_data'),
(87, 'Can delete nonveg_data', 29, 'delete_nonveg_data'),
(88, 'Can add special_request', 30, 'add_special_request'),
(89, 'Can change special_request', 30, 'change_special_request'),
(90, 'Can delete special_request', 30, 'delete_special_request'),
(91, 'Can add mess_meeting', 31, 'add_mess_meeting'),
(92, 'Can change mess_meeting', 31, 'change_mess_meeting'),
(93, 'Can delete mess_meeting', 31, 'delete_mess_meeting'),
(94, 'Can add menu_change_request', 32, 'add_menu_change_request'),
(95, 'Can change menu_change_request', 32, 'change_menu_change_request'),
(96, 'Can delete menu_change_request', 32, 'delete_menu_change_request'),
(97, 'Can add feedback', 33, 'add_feedback'),
(98, 'Can change feedback', 33, 'change_feedback'),
(99, 'Can delete feedback', 33, 'delete_feedback'),
(100, 'Can add caretaker', 34, 'add_caretaker'),
(101, 'Can change caretaker', 34, 'change_caretaker'),
(102, 'Can delete caretaker', 34, 'delete_caretaker'),
(103, 'Can add workers', 35, 'add_workers'),
(104, 'Can change workers', 35, 'change_workers'),
(105, 'Can delete workers', 35, 'delete_workers'),
(106, 'Can add student complain', 36, 'add_studentcomplain'),
(107, 'Can change student complain', 36, 'change_studentcomplain'),
(108, 'Can delete student complain', 36, 'delete_studentcomplain'),
(109, 'Can add file', 37, 'add_file'),
(110, 'Can change file', 37, 'change_file'),
(111, 'Can delete file', 37, 'delete_file'),
(112, 'Can add tracking', 38, 'add_tracking'),
(113, 'Can change tracking', 38, 'change_tracking'),
(114, 'Can delete tracking', 38, 'delete_tracking'),
(115, 'Can add department info', 39, 'add_departmentinfo'),
(116, 'Can change department info', 39, 'change_departmentinfo'),
(117, 'Can delete department info', 39, 'delete_departmentinfo'),
(118, 'Can add designation', 40, 'add_designation'),
(119, 'Can change designation', 40, 'change_designation'),
(120, 'Can delete designation', 40, 'delete_designation'),
(121, 'Can add extra info', 41, 'add_extrainfo'),
(122, 'Can change extra info', 41, 'change_extrainfo'),
(123, 'Can delete extra info', 41, 'delete_extrainfo'),
(124, 'Can add faculty', 42, 'add_faculty'),
(125, 'Can change faculty', 42, 'change_faculty'),
(126, 'Can delete faculty', 42, 'delete_faculty'),
(127, 'Can add staff', 43, 'add_staff'),
(128, 'Can change staff', 43, 'change_staff'),
(129, 'Can delete staff', 43, 'delete_staff'),
(130, 'Can add feedback', 44, 'add_feedback'),
(131, 'Can change feedback', 44, 'change_feedback'),
(132, 'Can delete feedback', 44, 'delete_feedback'),
(133, 'Can add holds designation', 45, 'add_holdsdesignation'),
(134, 'Can change holds designation', 45, 'change_holdsdesignation'),
(135, 'Can delete holds designation', 45, 'delete_holdsdesignation'),
(136, 'Can add issue', 46, 'add_issue'),
(137, 'Can change issue', 46, 'change_issue'),
(138, 'Can delete issue', 46, 'delete_issue'),
(139, 'Can add issue image', 47, 'add_issueimage'),
(140, 'Can change issue image', 47, 'change_issueimage'),
(141, 'Can delete issue image', 47, 'delete_issueimage'),
(142, 'Can add doctor', 48, 'add_doctor'),
(143, 'Can change doctor', 48, 'change_doctor'),
(144, 'Can delete doctor', 48, 'delete_doctor'),
(145, 'Can add health_ card', 49, 'add_health_card'),
(146, 'Can change health_ card', 49, 'change_health_card'),
(147, 'Can delete health_ card', 49, 'delete_health_card'),
(148, 'Can add prescription', 50, 'add_prescription'),
(149, 'Can change prescription', 50, 'change_prescription'),
(150, 'Can delete prescription', 50, 'delete_prescription'),
(151, 'Can add complaint', 51, 'add_complaint'),
(152, 'Can change complaint', 51, 'change_complaint'),
(153, 'Can delete complaint', 51, 'delete_complaint'),
(154, 'Can add stock', 52, 'add_stock'),
(155, 'Can change stock', 52, 'change_stock'),
(156, 'Can delete stock', 52, 'delete_stock'),
(157, 'Can add stockinventory', 53, 'add_stockinventory'),
(158, 'Can change stockinventory', 53, 'change_stockinventory'),
(159, 'Can delete stockinventory', 53, 'delete_stockinventory'),
(160, 'Can add prescribed_medicine', 54, 'add_prescribed_medicine'),
(161, 'Can change prescribed_medicine', 54, 'change_prescribed_medicine'),
(162, 'Can delete prescribed_medicine', 54, 'delete_prescribed_medicine'),
(163, 'Can add appointment', 55, 'add_appointment'),
(164, 'Can change appointment', 55, 'change_appointment'),
(165, 'Can delete appointment', 55, 'delete_appointment'),
(166, 'Can add ambulance_request', 56, 'add_ambulance_request'),
(167, 'Can change ambulance_request', 56, 'change_ambulance_request'),
(168, 'Can delete ambulance_request', 56, 'delete_ambulance_request'),
(169, 'Can add hospital_admit', 57, 'add_hospital_admit'),
(170, 'Can change hospital_admit', 57, 'change_hospital_admit'),
(171, 'Can delete hospital_admit', 57, 'delete_hospital_admit'),
(172, 'Can add course documents', 58, 'add_coursedocuments'),
(173, 'Can change course documents', 58, 'change_coursedocuments'),
(174, 'Can delete course documents', 58, 'delete_coursedocuments'),
(175, 'Can add course video', 59, 'add_coursevideo'),
(176, 'Can change course video', 59, 'change_coursevideo'),
(177, 'Can delete course video', 59, 'delete_coursevideo'),
(178, 'Can add quiz', 60, 'add_quiz'),
(179, 'Can change quiz', 60, 'change_quiz'),
(180, 'Can delete quiz', 60, 'delete_quiz'),
(181, 'Can add quiz question', 61, 'add_quizquestion'),
(182, 'Can change quiz question', 61, 'change_quizquestion'),
(183, 'Can delete quiz question', 61, 'delete_quizquestion'),
(184, 'Can add student answer', 62, 'add_studentanswer'),
(185, 'Can change student answer', 62, 'change_studentanswer'),
(186, 'Can delete student answer', 62, 'delete_studentanswer'),
(187, 'Can add assignment', 63, 'add_assignment'),
(188, 'Can change assignment', 63, 'change_assignment'),
(189, 'Can delete assignment', 63, 'delete_assignment'),
(190, 'Can add student assignment', 64, 'add_studentassignment'),
(191, 'Can change student assignment', 64, 'change_studentassignment'),
(192, 'Can delete student assignment', 64, 'delete_studentassignment'),
(193, 'Can add quiz result', 65, 'add_quizresult'),
(194, 'Can change quiz result', 65, 'change_quizresult'),
(195, 'Can delete quiz result', 65, 'delete_quizresult'),
(196, 'Can add forum', 66, 'add_forum'),
(197, 'Can change forum', 66, 'change_forum'),
(198, 'Can delete forum', 66, 'delete_forum'),
(199, 'Can add forum reply', 67, 'add_forumreply'),
(200, 'Can change forum reply', 67, 'change_forumreply'),
(201, 'Can delete forum reply', 67, 'delete_forumreply'),
(202, 'Can add project', 68, 'add_project'),
(203, 'Can change project', 68, 'change_project'),
(204, 'Can delete project', 68, 'delete_project'),
(205, 'Can add language', 69, 'add_language'),
(206, 'Can change language', 69, 'change_language'),
(207, 'Can delete language', 69, 'delete_language'),
(208, 'Can add know', 70, 'add_know'),
(209, 'Can change know', 70, 'change_know'),
(210, 'Can delete know', 70, 'delete_know'),
(211, 'Can add skill', 71, 'add_skill'),
(212, 'Can change skill', 71, 'change_skill'),
(213, 'Can delete skill', 71, 'delete_skill'),
(214, 'Can add has', 72, 'add_has'),
(215, 'Can change has', 72, 'change_has'),
(216, 'Can delete has', 72, 'delete_has'),
(217, 'Can add education', 73, 'add_education'),
(218, 'Can change education', 73, 'change_education'),
(219, 'Can delete education', 73, 'delete_education'),
(220, 'Can add experience', 74, 'add_experience'),
(221, 'Can change experience', 74, 'change_experience'),
(222, 'Can delete experience', 74, 'delete_experience'),
(223, 'Can add course', 75, 'add_course'),
(224, 'Can change course', 75, 'change_course'),
(225, 'Can delete course', 75, 'delete_course'),
(226, 'Can add publication', 76, 'add_publication'),
(227, 'Can change publication', 76, 'change_publication'),
(228, 'Can delete publication', 76, 'delete_publication'),
(229, 'Can add coauthor', 77, 'add_coauthor'),
(230, 'Can change coauthor', 77, 'change_coauthor'),
(231, 'Can delete coauthor', 77, 'delete_coauthor'),
(232, 'Can add patent', 78, 'add_patent'),
(233, 'Can change patent', 78, 'change_patent'),
(234, 'Can delete patent', 78, 'delete_patent'),
(235, 'Can add coinventor', 79, 'add_coinventor'),
(236, 'Can change coinventor', 79, 'change_coinventor'),
(237, 'Can delete coinventor', 79, 'delete_coinventor'),
(238, 'Can add interest', 80, 'add_interest'),
(239, 'Can change interest', 80, 'change_interest'),
(240, 'Can delete interest', 80, 'delete_interest'),
(241, 'Can add achievement', 81, 'add_achievement'),
(242, 'Can change achievement', 81, 'change_achievement'),
(243, 'Can delete achievement', 81, 'delete_achievement'),
(244, 'Can add message officer', 82, 'add_messageofficer'),
(245, 'Can change message officer', 82, 'change_messageofficer'),
(246, 'Can delete message officer', 82, 'delete_messageofficer'),
(247, 'Can add notify student', 83, 'add_notifystudent'),
(248, 'Can change notify student', 83, 'change_notifystudent'),
(249, 'Can delete notify student', 83, 'delete_notifystudent'),
(250, 'Can add placement status', 84, 'add_placementstatus'),
(251, 'Can change placement status', 84, 'change_placementstatus'),
(252, 'Can delete placement status', 84, 'delete_placementstatus'),
(253, 'Can add placement record', 85, 'add_placementrecord'),
(254, 'Can change placement record', 85, 'change_placementrecord'),
(255, 'Can delete placement record', 85, 'delete_placementrecord'),
(256, 'Can add student record', 86, 'add_studentrecord'),
(257, 'Can change student record', 86, 'change_studentrecord'),
(258, 'Can delete student record', 86, 'delete_studentrecord'),
(259, 'Can add chairman visit', 87, 'add_chairmanvisit'),
(260, 'Can change chairman visit', 87, 'change_chairmanvisit'),
(261, 'Can delete chairman visit', 87, 'delete_chairmanvisit'),
(262, 'Can add contact company', 88, 'add_contactcompany'),
(263, 'Can change contact company', 88, 'change_contactcompany'),
(264, 'Can delete contact company', 88, 'delete_contactcompany'),
(265, 'Can add placement schedule', 89, 'add_placementschedule'),
(266, 'Can change placement schedule', 89, 'change_placementschedule'),
(267, 'Can delete placement schedule', 89, 'delete_placementschedule'),
(268, 'Can add student placement', 90, 'add_studentplacement'),
(269, 'Can change student placement', 90, 'change_studentplacement'),
(270, 'Can delete student placement', 90, 'delete_studentplacement'),
(271, 'Can add award_and_scholarship', 91, 'add_award_and_scholarship'),
(272, 'Can change award_and_scholarship', 91, 'change_award_and_scholarship'),
(273, 'Can delete award_and_scholarship', 91, 'delete_award_and_scholarship'),
(274, 'Can add director_gold', 92, 'add_director_gold'),
(275, 'Can change director_gold', 92, 'change_director_gold'),
(276, 'Can delete director_gold', 92, 'delete_director_gold'),
(277, 'Can add director_silver', 93, 'add_director_silver'),
(278, 'Can change director_silver', 93, 'change_director_silver'),
(279, 'Can delete director_silver', 93, 'delete_director_silver'),
(280, 'Can add mcm', 94, 'add_mcm'),
(281, 'Can change mcm', 94, 'change_mcm'),
(282, 'Can delete mcm', 94, 'delete_mcm'),
(283, 'Can add notional_prize', 95, 'add_notional_prize'),
(284, 'Can change notional_prize', 95, 'change_notional_prize'),
(285, 'Can delete notional_prize', 95, 'delete_notional_prize'),
(286, 'Can add previous_winner', 96, 'add_previous_winner'),
(287, 'Can change previous_winner', 96, 'change_previous_winner'),
(288, 'Can delete previous_winner', 96, 'delete_previous_winner'),
(289, 'Can add proficiency_dm', 97, 'add_proficiency_dm'),
(290, 'Can change proficiency_dm', 97, 'change_proficiency_dm'),
(291, 'Can delete proficiency_dm', 97, 'delete_proficiency_dm'),
(292, 'Can add release', 98, 'add_release'),
(293, 'Can change release', 98, 'change_release'),
(294, 'Can delete release', 98, 'delete_release'),
(295, 'Can add visitor', 99, 'add_visitor'),
(296, 'Can change visitor', 99, 'change_visitor'),
(297, 'Can delete visitor', 99, 'delete_visitor'),
(298, 'Can add book_room', 100, 'add_book_room'),
(299, 'Can change book_room', 100, 'change_book_room'),
(300, 'Can delete book_room', 100, 'delete_book_room'),
(301, 'Can add visitor_bill', 101, 'add_visitor_bill'),
(302, 'Can change visitor_bill', 101, 'change_visitor_bill'),
(303, 'Can delete visitor_bill', 101, 'delete_visitor_bill'),
(304, 'Can add room', 102, 'add_room'),
(305, 'Can change room', 102, 'change_room'),
(306, 'Can delete room', 102, 'delete_room'),
(307, 'Can add visitor_room', 103, 'add_visitor_room'),
(308, 'Can change visitor_room', 103, 'change_visitor_room'),
(309, 'Can delete visitor_room', 103, 'delete_visitor_room'),
(310, 'Can add meal', 104, 'add_meal'),
(311, 'Can change meal', 104, 'change_meal'),
(312, 'Can delete meal', 104, 'delete_meal'),
(313, 'Can add inventory', 105, 'add_inventory'),
(314, 'Can change inventory', 105, 'change_inventory'),
(315, 'Can delete inventory', 105, 'delete_inventory'),
(316, 'Can add email address', 106, 'add_emailaddress'),
(317, 'Can change email address', 106, 'change_emailaddress'),
(318, 'Can delete email address', 106, 'delete_emailaddress'),
(319, 'Can add email confirmation', 107, 'add_emailconfirmation'),
(320, 'Can change email confirmation', 107, 'change_emailconfirmation'),
(321, 'Can delete email confirmation', 107, 'delete_emailconfirmation'),
(322, 'Can add social account', 108, 'add_socialaccount'),
(323, 'Can change social account', 108, 'change_socialaccount'),
(324, 'Can delete social account', 108, 'delete_socialaccount'),
(325, 'Can add social application', 109, 'add_socialapp'),
(326, 'Can change social application', 109, 'change_socialapp'),
(327, 'Can delete social application', 109, 'delete_socialapp'),
(328, 'Can add social application token', 110, 'add_socialtoken'),
(329, 'Can change social application token', 110, 'change_socialtoken'),
(330, 'Can delete social application token', 110, 'delete_socialtoken'),
(331, 'Can add common_info', 111, 'add_common_info'),
(332, 'Can change common_info', 111, 'change_common_info'),
(333, 'Can delete common_info', 111, 'delete_common_info');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user`
--

CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(1, 'pbkdf2_sha256$36000$1HLCGOlNe2Mi$j2jr2QAdC1SWPyryqYi87yHkR+aFcdGzAspv6yGUGkg=', '2018-03-28 08:24:56.815126', 1, 'balaji', 'Balaji', 'Segu', 'balaji@gmail.com', 1, 1, '2018-03-16 14:13:22.000000'),
(2, 'pbkdf2_sha256$36000$kRshsOxy792h$rcBtYL325axF7uaLjA5gpBCdvheXRVuUnVZZUI7bvIk=', '2018-03-28 08:21:37.472812', 1, 'subirs', '', '', '', 1, 1, '2018-03-16 14:26:33.000000'),
(3, 'pbkdf2_sha256$36000$d4jPAPkbGY1e$va6+T0hZJaJA6PiTA3ruuyWhgKgLKbpX9QEGrGvZtb8=', '2018-03-28 08:16:17.359844', 1, 'rajeshk', '', '', '', 1, 1, '2018-03-16 14:27:54.000000');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_groups`
--

CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_user_permissions`
--

CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `award_and_scholarship`
--

CREATE TABLE `award_and_scholarship` (
  `id` int(11) NOT NULL,
  `award_name` varchar(100) NOT NULL,
  `catalog` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `award_and_scholarship`
--

INSERT INTO `award_and_scholarship` (`id`, `award_name`, `catalog`) VALUES
(2, 'Director Gold Medal', '\"1. Director’s Gold Medals (DGMs), to be presented at the Institute Convocation every year, shall be awarded for the best all round performance from among the graduating (a) B Tech batch and (b) M Tech/M Des/PhD students. Students of all disciplines/programme shall be eligible for the award of DGM.  \r\n2. The all-round performance shall be judged by a separate committee appointed by the Chairman Senate. Criteria for short listing the candidates shall be laid down by the committee as per Section 2.4.1. However, a reporting CPI of 8.0 shall be the minimum requirement for the award of the Director’s Gold Medal. \r\n3. The student receiving the award should not have been involved in any act of indiscipline (except warning under clause 3.2.2.1 of SACS manual) during her/his entire academic programme. \r\n4. The DGMs shall be made out of 15 gm of 18 carat gold. \"'),
(3, 'Director Silver Medal Cultural', '\"1. Director’s Silver Medals (DSMs) shall be presented at the time of Institute’s Convocation for the outstanding performance in Cultural activities from among the graduating undergraduate and postgraduate students. \r\n2. The award of DSMs shall be decided by the separate committee appointed for this purpose by the Chairman, Academic Senate. The committee shall lay down the criteria for short listing the candidates before calling them for an interview. \r\n3.  Director’s Silver Medals shall be made out of 15 gm silver. \"'),
(4, 'IIITDM Proficiency Prizes', '\"IIITDM Proficiency Prizes is normally awarded for (i) the best B Tech project in the graduating BTech batch and (ii) the best thesis from among the graduating MTech./ M.Des./ PhD students in each of the discipline. The recipient(s) of the D&M Proficiency Gold Medals shall be eligible for the award of the IIITDM Proficiency Prizes \r\n \r\n4.5.1 IIITDM Proficiency Prizes shall be silver medals to be awarded at the time of Institute’s Convocation for (i) the best project in the graduating B Tech batch and (ii) the best thesis from the graduating M Tech/ MDes/ PhD students in each of the disciplines.In case a student’s program does not belong to any of the discipline, he may apply for any one of the discipline related to his major area of research. 4.5.2 The discipline committee constituted for this award for each discipline shall lay the minimum requirements for the award of Proficiency Prize and shall lay the criteria for short listing the applications received. 4.5.3 In the event of a group being awarded the best project award, each graduating member of the team shall be awarded the prize. 4.5.4 There will be separate prize for the M.Tech, M. Des. and Ph.D. Prize for Ph.D. will be awarded when there is enough competition i.e. 5 or more Ph.D. degree is awarded in that particular year. 4.5.5 Proficiency Prizes shall be made out of 15 gm silver.” 4.5.6  In the event of a group being awarded the best project, each individual student will be awarded the medal provided the student satisfies following eligibility criteria for the award.” (a) The students must have at least a CPI of 6.5. (b) At the time of application, there should not be any backlog of courses for the student. (c) Student’s grade in the project must be A, A+ or S.” \"'),
(5, 'Chairman Gold Medal', '\"1.The Chairman’s Gold Medal (CGM), to be presented at the Institute Convocation every year, shall be awarded to the student with the best academic performance in the entire graduating B Tech batch. However, a reporting CPI of 9.0 shall be the minimum requirement for the award of the Chairman’s Gold Medal.  \r\n2. The best academic performance shall be judged in terms of the reporting CPI. In the event of a tie in terms of the reporting CPI, the CPI shall be computed to the second decimal place in an attempt to break the tie. However, if there is still a tie, the CGM shall be awarded to as many students as are tied. No attempt shall be made to break the tie by computing the CPI to the third places of decimal and so on. \r\n3. The student receiving the award should not have been involved in any act of indiscipline (except warning under clause 3.2.2.1 of SACS manual) during her/his entire academic programme. \r\n4. The CGM shall be made out of 15 gm of 22 carat gold.\"'),
(6, 'Academic Performance Proficiency Silver Medal', '\"1. Academic Performance Proficiency Silver Medals shall be awarded at the time of Institute’s Convocation for the outstanding academic performance to the best graduating student of each discipline of the B Tech program. \r\n2. The recipient(s) of the Chairman’s Gold Medal shall be eligible for the award of the Academic Performance Proficiency Medal. \r\n3. The award of a Proficiency Medal may not be made for a particular discipline if the total number of graduating students for that discipline is less than five. \r\n4. The award of a Proficiency Medal may not be made for a particular discipline if the highest CPI among the graduating students of that discipline is less than 8.5. \r\n5. In the event of a tie, in terms of the reporting CPI, the medal shall be awarded to all the students, so tied, with no effort being made to break the tie. \r\n6. Academic Performance Proficiency Medals shall be made out of 15 gm silver\"'),
(7, 'Notional Prizes', '\"1. Notional Prizes and Certificates of Merit shall be awarded to 7 percent of the students of each undergraduate and postgraduate batch for excellent academic performance in an academic year. In the first two years, the 7 percent shall be calculated for the entire B Tech batch, whereas for the third year the award shall be made for each discipline taking into account their respective strengths. For PG student, the 7 percent shall be calculated based on the academic performance of the first two semester of PG program for each discipline taking into account their respective strengths. \r\n2. The Notional Prize may be awarded to a student irrespective of whether he/she is a recipient of any other scholarship or not. \r\n3. The value of the Notional Prize shall be as prescribed from time to time, by the Ministry of Human Resources and Development.\r\n4. In calculating the actual number of awards to be made in any year or for any department, any fraction shall usually be rounded off to the next integer. However, this may not be done in those cases where there is a significant difference in the performance level of the students. \r\n5. The award shall, in principle, be given only on the basis of the annual performance. (By dividing credits earned in two regular semester with total credits for two semester) Further the award may not be made for any department having student strength of less than 5. It may also not be made if the highest CPI for any department is considerably lower than the performance levels at which the award is being made for other departments or minimum CPI limit of 8.5.\"'),
(8, 'Mcm', '\"Eligibility Requirements : 1. Minimum CPI : Minimum reporting CPI (6.0 for GENERAL Category Students and 5.5 for SC/ST students) at the end of previous semester.\n2. Family annual income certificate (Form A or Form B or Form C) : The parental/guardian family annual income of a student and from all sources in the preceeding financial year must not exceed 2.50 Lakhs. Please note that income certificate is properly sealed and signed bu Competent Revenue authority of Government of India. (Normally issued by District Magistrate / Tehsildat in original). Please enclosed the parental/guardian family income in the prescribed format(A,B,or C) as  applicable.\n\nFor more details refer to Institute SPACS manual.\"'),
(9, 'Director Silver Medal Games and Sports', '\"1. Director’s Silver Medals (DSMs) shall be presented at the time of Institute’s Convocation for the outstanding performance in Games & Sports activities from among the graduating undergraduate and postgraduate students. \r\n2. The award of DSMs shall be decided by the separate committee appointed for this purpose by the Chairman, Academic Senate. The committee shall lay down the criteria for short listing the candidates before calling them for an interview. \r\n3.  Director’s Silver Medals shall be made out of 15 gm silver. \"'),
(10, 'D&M Proficiency Gold Medal', '\"1. Design and Manufacturing Proficiency Gold Medals are awarded at the time of Institute’s Convocation for the best cross-disciplinary project from among the graduating BTech students and the best cross-disciplinary thesis from among the graduating MTech / MDes / PhD students. Award of design and manufacturing proficiency gold medal (D&MPGM) is applicable for BTP/PBI or Design and Fabrication projects. \r\n2. The award of D&M Proficiency Gold Medals shall be decided by the separate committee appointed for this purpose by the Chairman, Academic Senate which will seek applications after finalizing a short listing criterion. After short listing of applications, the committee shall call all the short listed applicants for a presentation/demonstration.   \r\n3. D&M Proficiency Gold Medals may not be awarded if projects/theses submitted for the award are found to have an inadequate cross-disciplinary content. \r\n4. The D&M Proficiency Gold Medals shall be made out of 15 gm of 18 carat gold. \r\n5. In the event of a group being awarded the best cross-disciplinary project, each individual student shall be awarded the medal provided the student satisfies following eligibility criteria for the award. (a) The students must have at least a CPI of 6.5. (b) At the time of application, there should not be any backlog of courses for the student. (c) Student’s grade in the project must be A, A+ or S.” \"');

-- --------------------------------------------------------

--
-- Table structure for table `calendar`
--

CREATE TABLE `calendar` (
  `id` int(11) NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `description` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `course`
--

CREATE TABLE `course` (
  `id` int(11) NOT NULL,
  `course_id` varchar(100) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `sem` int(11) NOT NULL,
  `credits` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `director_gold`
--

CREATE TABLE `director_gold` (
  `id` int(11) NOT NULL,
  `status` varchar(10) NOT NULL,
  `correspondence_address` varchar(100) DEFAULT NULL,
  `nearest_policestation` varchar(25) DEFAULT NULL,
  `nearest_railwaystation` varchar(25) DEFAULT NULL,
  `relevant_document` varchar(100) DEFAULT NULL,
  `date` date NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `award_id_id` int(11) NOT NULL,
  `academic_achievements` longtext,
  `coorporate` longtext,
  `counselling_activities` longtext,
  `cultural_inside` longtext,
  `cultural_outside` longtext,
  `financial_assistance` longtext,
  `games_inside` longtext,
  `games_outside` longtext,
  `grand_total` int(11) DEFAULT NULL,
  `gymkhana_activities` longtext,
  `hall_activities` longtext,
  `institute_activities` longtext,
  `justification` longtext,
  `other_activities` longtext,
  `science_inside` longtext,
  `science_outside` longtext,
  `social` longtext
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `director_gold`
--

INSERT INTO `director_gold` (`id`, `status`, `correspondence_address`, `nearest_policestation`, `nearest_railwaystation`, `relevant_document`, `date`, `student_id`, `award_id_id`, `academic_achievements`, `coorporate`, `counselling_activities`, `cultural_inside`, `cultural_outside`, `financial_assistance`, `games_inside`, `games_outside`, `grand_total`, `gymkhana_activities`, `hall_activities`, `institute_activities`, `justification`, `other_activities`, `science_inside`, `science_outside`, `social`) VALUES
(1, 'Accept', 'kj', ';dfj', 'jfkajdf', '', '2018-03-17', '2015335', 4, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(5, 'Accept', 'adress', 'station', 'station', 'segu_balaji_resume_36JgSSb.pdf', '2018-03-22', '2015335', 2, 'asdhfjk', 'sdfsdf', 'fsdf', 'sdf', 'sdfd', NULL, 'sdf', 'sdf', NULL, 'asdfsd', 'sdf', 'fsdfsd', 'sdf', NULL, 'jhsadlfkj', 'jslhdkf', 'sdf'),
(6, 'Accept', 'akdjsf', 'kljsasdlfjk', 'kljKLEJ', 'segubalaji.png', '2018-03-24', '2015335', 2, 'KADJLK', 'KJSADKFJ', 'JKLSDJFKLJLKJ', 'LKJSAKDSFJ', 'JKLSDJFLKJKSJFK', 'KJASLFKDJ', 'AKSDJFLKJ', 'KJKJKLDFJ', 5, 'JSDKJFLKJ', 'KJKFJLK', 'KLJSKLFJLK', 'KSDDKFJLK', NULL, 'KLASDLKFJKJ', 'KSDKLFJLJ', 'KDJFKLJ'),
(7, 'COMPLETE', 'ajfkl', 'lkjaksldfj', 'kljlskjf', 'student.xlsx', '2018-03-25', '2015335', 2, 'aksjdfhkasflk', 'lkj', 'jl', 'jlk', 'jlk', NULL, 'lkjkl', 'jlk', 250, 'kjlkj', 'lkj', 'kjk', 'klj', NULL, 'kjalkj', 'lkj', 'j');

-- --------------------------------------------------------

--
-- Table structure for table `director_silver`
--

CREATE TABLE `director_silver` (
  `id` int(11) NOT NULL,
  `nearest_policestation` varchar(25) DEFAULT NULL,
  `nearest_railwaystation` varchar(25) DEFAULT NULL,
  `correspondence_address` varchar(100) DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `relevant_document` varchar(100) DEFAULT NULL,
  `date` date NOT NULL,
  `award_id_id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `inside_achievements` longtext,
  `financial_assistance` longtext,
  `grand_total` int(11) DEFAULT NULL,
  `justification` longtext,
  `outside_achievements` longtext
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `director_silver`
--

INSERT INTO `director_silver` (`id`, `nearest_policestation`, `nearest_railwaystation`, `correspondence_address`, `status`, `relevant_document`, `date`, `award_id_id`, `student_id`, `inside_achievements`, `financial_assistance`, `grand_total`, `justification`, `outside_achievements`) VALUES
(1, 'kasjd;fj', 'kjs;dfkja', 'dkfja;kj', 'COMPLETE', '', '2018-03-17', 3, '2015335', NULL, NULL, NULL, NULL, NULL),
(2, 'adf', 'asdf', 'fadf', 'COMPLETE', '', '2018-03-18', 3, '2015335', NULL, NULL, NULL, NULL, NULL),
(3, 'adf', 'asdf', 'fadf', 'INCOMPLETE', '', '2018-03-18', 9, '2015335', NULL, NULL, NULL, NULL, NULL),
(4, 'asdf', 'sadf', 'adf', 'COMPLETE', '__init___aSF8Lbb.py', '2018-03-18', 3, '2015335', 'dfgads', 'adf', NULL, 'sfgdfsg', 'sgdfg'),
(5, 'jahsdfj', 'jhf', 'djfh', 'INCOMPLETE', 'SPACS_data_ckWWReh.xlsx', '2018-03-18', 3, '2015335', 'jf', 'asjdhf', NULL, 'sdfjk', 'sdkf'),
(6, 'station', 'station', NULL, 'INCOMPLETE', 'segu_balaji_resume.pdf', '2018-03-22', 3, '2015335', 'dfjkla', NULL, NULL, 'kjsadfkl;j', 'kjsdkfj'),
(7, 'station', 'station', NULL, 'INCOMPLETE', 'segu_balaji_resume_Jtar5lr.pdf', '2018-03-22', 9, '2015335', 'sdjf', NULL, NULL, 'kjsd;fklj', 'kjasd;lgj'),
(8, 'station', 'station', NULL, 'INCOMPLETE', 'Academic_Calendar_2017-2018.pdf', '2018-03-22', 9, '2015335', 'jfkbasdkjlfb', NULL, NULL, 'flaijshglkjashfgjkl', 'lfdiajkgjh'),
(9, 'station', 'station', NULL, 'INCOMPLETE', 'Academic_Calendar_2017-2018_lAOhZr2.pdf', '2018-03-22', 9, '2015335', 'jfkbasdkjlfb', NULL, NULL, 'flaijshglkjashfgjkl', 'lfdiajkgjh'),
(10, 'station', 'station', NULL, 'INCOMPLETE', 'Academic_Calendar_2017-2018_oLW4EB7.pdf', '2018-03-22', 9, '2015335', 'jfkbasdkjlfb', NULL, NULL, 'flaijshglkjashfgjkl', 'lfdiajkgjh'),
(11, 'kdkfjlkjadlfj', 'ksadjflk', 'asdjfk', 'INCOMPLETE', '', '2018-03-25', 9, '2015335', 'ksdnfk', NULL, 2500, ';ksdjfl', 'sdkfk');

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_admin_log`
--

INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES
(1, '2018-03-16 14:15:46.547001', '1', 'spacsassistant', 1, '[{\"added\": {}}]', 40, 1),
(2, '2018-03-16 14:16:04.061536', '2', 'spacsconvenor', 1, '[{\"added\": {}}]', 40, 1),
(3, '2018-03-16 14:16:18.203805', '3', 'student', 1, '[{\"added\": {}}]', 40, 1),
(4, '2018-03-16 14:20:35.192998', '1', 'department: CSE', 1, '[{\"added\": {}}]', 39, 1),
(5, '2018-03-16 14:20:48.407614', '2', 'department: ECE', 1, '[{\"added\": {}}]', 39, 1),
(6, '2018-03-16 14:21:00.401362', '3', 'department: MECH', 1, '[{\"added\": {}}]', 39, 1),
(7, '2018-03-16 14:21:31.156995', '4', 'department: Design', 1, '[{\"added\": {}}]', 39, 1),
(8, '2018-03-16 14:23:02.066320', '2015335', '2015335 - balaji', 1, '[{\"added\": {}}]', 41, 1),
(9, '2018-03-16 14:26:33.748059', '2', 'subirs', 1, '[{\"added\": {}}]', 4, 1),
(10, '2018-03-16 14:27:23.098601', '2', 'subirs', 2, '[{\"changed\": {\"fields\": [\"is_staff\", \"is_superuser\"]}}]', 4, 1),
(11, '2018-03-16 14:27:54.530832', '3', 'rajeshk', 1, '[{\"added\": {}}]', 4, 1),
(12, '2018-03-16 14:28:10.344688', '3', 'rajeshk', 2, '[{\"changed\": {\"fields\": [\"is_staff\", \"is_superuser\"]}}]', 4, 1),
(13, '2018-03-16 14:30:10.757488', '75', '75 - rajeshk', 1, '[{\"added\": {}}]', 41, 1),
(14, '2018-03-16 14:30:55.657391', '85', '85 - subirs', 1, '[{\"added\": {}}]', 41, 1),
(15, '2018-03-16 14:31:56.423888', '1', 'rajeshk is spacsassistant', 1, '[{\"added\": {}}]', 45, 1),
(16, '2018-03-16 14:32:13.926158', '2', 'subirs is spacsconvenor', 1, '[{\"added\": {}}]', 45, 1),
(17, '2018-03-17 01:50:23.303498', '1', 'D&M proficiency gold medal', 1, '[{\"added\": {}}]', 91, 2),
(18, '2018-03-17 01:50:54.126564', '2', 'Director Gold Medal', 1, '[{\"added\": {}}]', 91, 2),
(19, '2018-03-17 01:51:48.327121', '3', 'Director Silver Medal', 1, '[{\"added\": {}}]', 91, 2),
(20, '2018-03-17 01:52:37.018872', '4', 'IIITDM Proficiency Prizes', 1, '[{\"added\": {}}]', 91, 2),
(21, '2018-03-17 01:53:14.219306', '5', 'Chairman Gold medal', 1, '[{\"added\": {}}]', 91, 2),
(22, '2018-03-17 01:54:00.153345', '6', 'Academic Performance Proficiency Silver Medal', 1, '[{\"added\": {}}]', 91, 2),
(23, '2018-03-17 02:01:28.982863', '5', 'Chairman Gold Medal', 2, '[{\"changed\": {\"fields\": [\"award_name\"]}}]', 91, 2),
(24, '2018-03-17 02:01:54.847886', '1', 'D&M Proficiency Gold Medal', 2, '[{\"changed\": {\"fields\": [\"award_name\"]}}]', 91, 2),
(25, '2018-03-17 02:14:49.839404', '7', 'Notional Prizes', 1, '[{\"added\": {}}]', 91, 2),
(26, '2018-03-17 02:35:16.301667', '2015335', '2015335 - balaji', 1, '[{\"added\": {}}]', 19, 2),
(27, '2018-03-17 05:34:28.176725', '8', 'Mcm', 1, '[{\"added\": {}}]', 91, 2),
(28, '2018-03-17 05:34:53.270750', '3', 'Director Silver Medal Cultural', 2, '[{\"changed\": {\"fields\": [\"award_name\"]}}]', 91, 2),
(29, '2018-03-17 05:35:18.670315', '9', 'Director Silver Medal Games and Sports', 1, '[{\"added\": {}}]', 91, 2),
(30, '2018-03-17 07:32:22.462817', '1', 'D&M Proficiency Gold Medal', 2, '[]', 91, 1),
(31, '2018-03-17 07:35:29.789729', '1', 'D&M Proficiency Gold Medal', 3, '', 91, 1),
(32, '2018-03-17 07:35:55.273836', '10', 'D&M Proficiency Gold Medal', 1, '[{\"added\": {}}]', 91, 1),
(33, '2018-03-18 01:19:33.152197', '3', 'Director Silver Medal Cultural', 2, '[]', 91, 1),
(34, '2018-03-18 08:39:35.182857', '5', 'Chairman Gold Medal', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(35, '2018-03-18 08:39:57.203582', '2', 'Director Gold Medal', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(36, '2018-03-18 08:40:16.169915', '10', 'D&M Proficiency Gold Medal', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(37, '2018-03-18 08:40:50.699147', '6', 'Academic Performance Proficiency Silver Medal', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(38, '2018-03-18 08:41:22.423982', '4', 'IIITDM Proficiency Prizes', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(39, '2018-03-18 08:41:38.914464', '8', 'Mcm', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(40, '2018-03-18 08:42:07.124072', '7', 'Notional Prizes', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(41, '2018-03-18 08:42:31.371090', '3', 'Director Silver Medal Cultural', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(42, '2018-03-18 08:43:10.092670', '9', 'Director Silver Medal Games and Sports', 2, '[{\"changed\": {\"fields\": [\"catalog\"]}}]', 91, 1),
(43, '2018-03-18 08:43:42.255472', '3', 'Director Silver Medal Cultural', 2, '[]', 91, 1),
(44, '2018-03-19 19:13:11.334390', '2', 'Previous_winner object', 1, '[{\"added\": {}}]', 96, 1),
(45, '2018-03-21 14:00:37.409253', '2015335', '2015335 - balaji', 2, '[{\"changed\": {\"fields\": [\"phone_no\"]}}]', 41, 1),
(46, '2018-03-22 16:07:51.782433', '3', 'Previous_winner object', 1, '[{\"added\": {}}]', 96, 1),
(47, '2018-03-22 16:08:19.493705', '3', 'Previous_winner object', 2, '[]', 96, 1),
(48, '2018-03-22 16:13:47.539584', '1', 'balaji', 2, '[{\"changed\": {\"fields\": [\"first_name\", \"last_name\"]}}]', 4, 1),
(49, '2018-03-22 16:16:04.859529', '4', 'Previous_winner object', 1, '[{\"added\": {}}]', 96, 1),
(50, '2018-03-23 15:39:10.075705', '5', 'Proficiency_dm object', 3, '', 97, 1),
(51, '2018-03-23 15:39:10.163704', '4', 'Proficiency_dm object', 3, '', 97, 1),
(52, '2018-03-23 15:39:10.215705', '3', 'Proficiency_dm object', 3, '', 97, 1),
(53, '2018-03-23 15:39:10.303705', '2', 'Proficiency_dm object', 3, '', 97, 1),
(54, '2018-03-23 15:39:10.327704', '1', 'Proficiency_dm object', 3, '', 97, 1),
(55, '2018-03-23 15:40:25.621557', '4', 'Director_gold object', 3, '', 92, 1),
(56, '2018-03-23 15:40:25.715578', '3', 'Director_gold object', 3, '', 92, 1),
(57, '2018-03-23 15:40:25.775715', '2', 'Director_gold object', 3, '', 92, 1),
(58, '2018-03-23 15:40:50.462597', '3', '2015335 - balaji', 3, '', 94, 1),
(59, '2018-03-23 15:40:50.550612', '2', '2015335 - balaji', 3, '', 94, 1),
(60, '2018-03-23 15:40:50.614594', '1', '2015335 - balaji', 3, '', 94, 1),
(61, '2018-03-24 12:06:55.992948', '1', 'Common_info object', 3, '', 111, 1),
(62, '2018-03-24 12:16:43.412127', '2', 'Common_info object', 1, '[{\"added\": {}}]', 111, 1),
(63, '2018-03-24 12:26:56.293316', '2', 'Common_info object', 2, '[]', 111, 1);

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(11, 'academic_information', 'calendar'),
(12, 'academic_information', 'course'),
(13, 'academic_information', 'exam_timetable'),
(14, 'academic_information', 'grades'),
(15, 'academic_information', 'holiday'),
(16, 'academic_information', 'instructor'),
(17, 'academic_information', 'meeting'),
(18, 'academic_information', 'spi'),
(19, 'academic_information', 'student'),
(20, 'academic_information', 'student_attendance'),
(21, 'academic_information', 'timetable'),
(10, 'academic_procedures', 'finalregistrations'),
(8, 'academic_procedures', 'register'),
(9, 'academic_procedures', 'thesis'),
(106, 'account', 'emailaddress'),
(107, 'account', 'emailconfirmation'),
(1, 'admin', 'logentry'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(4, 'auth', 'user'),
(33, 'central_mess', 'feedback'),
(25, 'central_mess', 'menu'),
(32, 'central_mess', 'menu_change_request'),
(22, 'central_mess', 'mess'),
(31, 'central_mess', 'mess_meeting'),
(23, 'central_mess', 'monthly_bill'),
(29, 'central_mess', 'nonveg_data'),
(28, 'central_mess', 'nonveg_menu'),
(24, 'central_mess', 'payments'),
(26, 'central_mess', 'rebate'),
(30, 'central_mess', 'special_request'),
(27, 'central_mess', 'vacation_food'),
(34, 'complaint_system', 'caretaker'),
(36, 'complaint_system', 'studentcomplain'),
(35, 'complaint_system', 'workers'),
(5, 'contenttypes', 'contenttype'),
(37, 'file_tracking', 'file'),
(38, 'file_tracking', 'tracking'),
(39, 'globals', 'departmentinfo'),
(40, 'globals', 'designation'),
(41, 'globals', 'extrainfo'),
(42, 'globals', 'faculty'),
(44, 'globals', 'feedback'),
(45, 'globals', 'holdsdesignation'),
(46, 'globals', 'issue'),
(47, 'globals', 'issueimage'),
(43, 'globals', 'staff'),
(56, 'health_center', 'ambulance_request'),
(55, 'health_center', 'appointment'),
(51, 'health_center', 'complaint'),
(48, 'health_center', 'doctor'),
(49, 'health_center', 'health_card'),
(57, 'health_center', 'hospital_admit'),
(54, 'health_center', 'prescribed_medicine'),
(50, 'health_center', 'prescription'),
(52, 'health_center', 'stock'),
(53, 'health_center', 'stockinventory'),
(63, 'online_cms', 'assignment'),
(58, 'online_cms', 'coursedocuments'),
(59, 'online_cms', 'coursevideo'),
(66, 'online_cms', 'forum'),
(67, 'online_cms', 'forumreply'),
(60, 'online_cms', 'quiz'),
(61, 'online_cms', 'quizquestion'),
(65, 'online_cms', 'quizresult'),
(62, 'online_cms', 'studentanswer'),
(64, 'online_cms', 'studentassignment'),
(81, 'placement_cell', 'achievement'),
(87, 'placement_cell', 'chairmanvisit'),
(77, 'placement_cell', 'coauthor'),
(79, 'placement_cell', 'coinventor'),
(88, 'placement_cell', 'contactcompany'),
(75, 'placement_cell', 'course'),
(73, 'placement_cell', 'education'),
(74, 'placement_cell', 'experience'),
(72, 'placement_cell', 'has'),
(80, 'placement_cell', 'interest'),
(70, 'placement_cell', 'know'),
(69, 'placement_cell', 'language'),
(82, 'placement_cell', 'messageofficer'),
(83, 'placement_cell', 'notifystudent'),
(78, 'placement_cell', 'patent'),
(85, 'placement_cell', 'placementrecord'),
(89, 'placement_cell', 'placementschedule'),
(84, 'placement_cell', 'placementstatus'),
(68, 'placement_cell', 'project'),
(76, 'placement_cell', 'publication'),
(71, 'placement_cell', 'skill'),
(90, 'placement_cell', 'studentplacement'),
(86, 'placement_cell', 'studentrecord'),
(91, 'scholarships', 'award_and_scholarship'),
(111, 'scholarships', 'common_info'),
(92, 'scholarships', 'director_gold'),
(93, 'scholarships', 'director_silver'),
(94, 'scholarships', 'mcm'),
(95, 'scholarships', 'notional_prize'),
(96, 'scholarships', 'previous_winner'),
(97, 'scholarships', 'proficiency_dm'),
(98, 'scholarships', 'release'),
(6, 'sessions', 'session'),
(7, 'sites', 'site'),
(108, 'socialaccount', 'socialaccount'),
(109, 'socialaccount', 'socialapp'),
(110, 'socialaccount', 'socialtoken'),
(100, 'visitor_hostel', 'book_room'),
(105, 'visitor_hostel', 'inventory'),
(104, 'visitor_hostel', 'meal'),
(102, 'visitor_hostel', 'room'),
(99, 'visitor_hostel', 'visitor'),
(101, 'visitor_hostel', 'visitor_bill'),
(103, 'visitor_hostel', 'visitor_room');

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2018-03-16 14:10:25.589522'),
(2, 'auth', '0001_initial', '2018-03-16 14:10:36.379539'),
(3, 'globals', '0001_initial', '2018-03-16 14:10:43.819904'),
(4, 'academic_information', '0001_initial', '2018-03-16 14:10:57.940173'),
(5, 'account', '0001_initial', '2018-03-16 14:11:00.739431'),
(6, 'account', '0002_email_max_length', '2018-03-16 14:11:02.274259'),
(7, 'admin', '0001_initial', '2018-03-16 14:11:04.294626'),
(8, 'admin', '0002_logentry_remove_auto_add', '2018-03-16 14:11:04.406831'),
(9, 'contenttypes', '0002_remove_content_type_name', '2018-03-16 14:11:05.440452'),
(10, 'auth', '0002_alter_permission_name_max_length', '2018-03-16 14:11:06.372695'),
(11, 'auth', '0003_alter_user_email_max_length', '2018-03-16 14:11:07.311559'),
(12, 'auth', '0004_alter_user_username_opts', '2018-03-16 14:11:07.461283'),
(13, 'auth', '0005_alter_user_last_login_null', '2018-03-16 14:11:07.888600'),
(14, 'auth', '0006_require_contenttypes_0002', '2018-03-16 14:11:07.908940'),
(15, 'auth', '0007_alter_validators_add_error_messages', '2018-03-16 14:11:08.001818'),
(16, 'auth', '0008_alter_user_username_max_length', '2018-03-16 14:11:08.809748'),
(17, 'globals', '0002_auto_20180209_2041', '2018-03-16 14:11:23.681973'),
(18, 'scholarships', '0001_initial', '2018-03-16 14:11:35.742326'),
(19, 'scholarships', '0002_notional_prize_award_id', '2018-03-16 14:11:37.149195'),
(20, 'sessions', '0001_initial', '2018-03-16 14:11:38.602149'),
(21, 'sites', '0001_initial', '2018-03-16 14:11:39.234853'),
(22, 'sites', '0002_alter_domain_unique', '2018-03-16 14:11:39.476421'),
(23, 'socialaccount', '0001_initial', '2018-03-16 14:11:46.149492'),
(24, 'socialaccount', '0002_token_max_lengths', '2018-03-16 14:11:49.205921'),
(25, 'socialaccount', '0003_extra_data_default_dict', '2018-03-16 14:11:49.396799'),
(26, 'scholarships', '0003_auto_20180317_0829', '2018-03-17 02:59:47.785872'),
(27, 'scholarships', '0004_auto_20180317_1220', '2018-03-17 06:51:13.418879'),
(28, 'scholarships', '0005_auto_20180317_1743', '2018-03-17 12:13:41.057658'),
(29, 'scholarships', '0006_auto_20180317_2355', '2018-03-17 18:25:35.716940'),
(30, 'scholarships', '0007_auto_20180318_0044', '2018-03-17 19:15:07.016876'),
(31, 'scholarships', '0008_auto_20180318_0656', '2018-03-18 01:26:25.797123'),
(32, 'scholarships', '0009_auto_20180318_0712', '2018-03-18 01:42:58.026376'),
(33, 'scholarships', '0010_auto_20180318_1000', '2018-03-18 04:31:09.346332'),
(34, 'scholarships', '0011_auto_20180322_2042', '2018-03-22 15:12:44.931707'),
(35, 'scholarships', '0012_common_info', '2018-03-24 04:30:07.287719'),
(36, 'scholarships', '0013_auto_20180324_1844', '2018-03-24 13:14:59.374747'),
(37, 'scholarships', '0014_auto_20180328_0835', '2018-03-28 03:05:34.668974'),
(38, 'scholarships', '0015_auto_20180328_0913', '2018-03-28 03:43:42.341218');

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('cbq8elfito86oxdbrgpznsc13qdpt9co', 'MTYxYzE0YWQ2NTRkMmUyNGUyNGM4MzQzMTg2OWYwMzY0ZGU2NzkyODp7Il9hdXRoX3VzZXJfaWQiOiIzIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI5N2U5MWRjNWY2YmE4YjJhZTZjMGM4NjZjNGQxY2NiNjUxZTFjYWY0IiwiX3Nlc3Npb25fZXhwaXJ5IjowfQ==', '2018-04-07 15:02:10.945793'),
('gaeouk83ob5iomf19u6idsm2n4n9dbjl', 'OGY1NmYxYjE4NDMyZTllYzU5MDdhNTQzNzg4YTc4M2UyYmMzZDliYjp7Il9hdXRoX3VzZXJfaWQiOiIyIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJiZWY4MGQ4ODQxNmEwN2U5NmNmZDRiZWE1MzQ0MzJkMGU4YzYwMjQyIiwiX3Nlc3Npb25fZXhwaXJ5IjowfQ==', '2018-04-01 11:18:06.051120');

-- --------------------------------------------------------

--
-- Table structure for table `django_site`
--

CREATE TABLE `django_site` (
  `id` int(11) NOT NULL,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `django_site`
--

INSERT INTO `django_site` (`id`, `domain`, `name`) VALUES
(1, 'example.com', 'example.com');

-- --------------------------------------------------------

--
-- Table structure for table `exam_timetable`
--

CREATE TABLE `exam_timetable` (
  `id` int(11) NOT NULL,
  `upload_date` date NOT NULL,
  `exam_time_table` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_departmentinfo`
--

CREATE TABLE `globals_departmentinfo` (
  `id` int(11) NOT NULL,
  `name` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `globals_departmentinfo`
--

INSERT INTO `globals_departmentinfo` (`id`, `name`) VALUES
(1, 'CSE'),
(4, 'Design'),
(2, 'ECE'),
(3, 'MECH');

-- --------------------------------------------------------

--
-- Table structure for table `globals_designation`
--

CREATE TABLE `globals_designation` (
  `id` int(11) NOT NULL,
  `name` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `globals_designation`
--

INSERT INTO `globals_designation` (`id`, `name`) VALUES
(1, 'spacsassistant'),
(2, 'spacsconvenor'),
(3, 'student');

-- --------------------------------------------------------

--
-- Table structure for table `globals_extrainfo`
--

CREATE TABLE `globals_extrainfo` (
  `id` varchar(20) NOT NULL,
  `sex` varchar(2) NOT NULL,
  `age` int(11) NOT NULL,
  `address` longtext NOT NULL,
  `phone_no` bigint(20) NOT NULL,
  `user_type` varchar(20) NOT NULL,
  `profile_picture` varchar(100) DEFAULT NULL,
  `about_me` longtext NOT NULL,
  `department_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `globals_extrainfo`
--

INSERT INTO `globals_extrainfo` (`id`, `sex`, `age`, `address`, `phone_no`, `user_type`, `profile_picture`, `about_me`, `department_id`, `user_id`) VALUES
('2015335', 'M', 18, 'jabalpur', 9479877619, 'student', '', 'ntg', 1, 1),
('75', 'M', 30, 'jabalpur', 1234567832, 'staff', '', '', NULL, 3),
('85', 'M', 33, 'jabalpur', 263547811, 'faculty', '', '', NULL, 2);

-- --------------------------------------------------------

--
-- Table structure for table `globals_faculty`
--

CREATE TABLE `globals_faculty` (
  `id_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_feedback`
--

CREATE TABLE `globals_feedback` (
  `id` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `feedback` longtext NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_holdsdesignation`
--

CREATE TABLE `globals_holdsdesignation` (
  `id` int(11) NOT NULL,
  `held_at` datetime(6) NOT NULL,
  `designation_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `working_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `globals_holdsdesignation`
--

INSERT INTO `globals_holdsdesignation` (`id`, `held_at`, `designation_id`, `user_id`, `working_id`) VALUES
(1, '2018-03-16 14:31:56.327766', 1, 3, 3),
(2, '2018-03-16 14:32:13.926158', 2, 2, 2);

-- --------------------------------------------------------

--
-- Table structure for table `globals_issue`
--

CREATE TABLE `globals_issue` (
  `id` int(11) NOT NULL,
  `report_type` varchar(63) NOT NULL,
  `module` varchar(63) NOT NULL,
  `closed` tinyint(1) NOT NULL,
  `text` longtext NOT NULL,
  `title` varchar(255) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `added_on` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_issueimage`
--

CREATE TABLE `globals_issueimage` (
  `id` int(11) NOT NULL,
  `image` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_issue_images`
--

CREATE TABLE `globals_issue_images` (
  `id` int(11) NOT NULL,
  `issue_id` int(11) NOT NULL,
  `issueimage_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_issue_support`
--

CREATE TABLE `globals_issue_support` (
  `id` int(11) NOT NULL,
  `issue_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `globals_staff`
--

CREATE TABLE `globals_staff` (
  `id_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `grades`
--

CREATE TABLE `grades` (
  `id` int(11) NOT NULL,
  `sem` int(11) NOT NULL,
  `grade` varchar(4) NOT NULL,
  `course_id_id` int(11) NOT NULL,
  `student_id_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `holiday`
--

CREATE TABLE `holiday` (
  `id` int(11) NOT NULL,
  `holiday_date` date NOT NULL,
  `holiday_name` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `instructor`
--

CREATE TABLE `instructor` (
  `id` int(11) NOT NULL,
  `course_id_id` int(11) NOT NULL,
  `instructor_id_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `mcm`
--

CREATE TABLE `mcm` (
  `id` int(11) NOT NULL,
  `brother_name` varchar(30) DEFAULT NULL,
  `brother_occupation` longtext,
  `sister_name` varchar(30) DEFAULT NULL,
  `sister_occupation` longtext,
  `income_father` int(11) NOT NULL,
  `income_mother` int(11) NOT NULL,
  `income_other` int(11) NOT NULL,
  `father_occ` varchar(10) NOT NULL,
  `mother_occ` varchar(10) NOT NULL,
  `forms` varchar(100) DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `annual_income` int(11) NOT NULL,
  `date` date NOT NULL,
  `award_id_id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `bank_name` varchar(10) DEFAULT NULL,
  `college_fee` int(11) DEFAULT NULL,
  `college_name` varchar(30) DEFAULT NULL,
  `constructed_area` int(11) DEFAULT NULL,
  `father_occ_desc` varchar(30) DEFAULT NULL,
  `four_wheeler` int(11) DEFAULT NULL,
  `four_wheeler_desc` varchar(30) DEFAULT NULL,
  `house` varchar(10) DEFAULT NULL,
  `income_certificate` varchar(100) DEFAULT NULL,
  `loan_amount` int(11) DEFAULT NULL,
  `mother_occ_desc` varchar(30) DEFAULT NULL,
  `plot_area` int(11) DEFAULT NULL,
  `school_fee` int(11) DEFAULT NULL,
  `school_name` varchar(30) DEFAULT NULL,
  `two_wheeler` int(11) DEFAULT NULL,
  `two_wheeler_desc` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `mcm`
--

INSERT INTO `mcm` (`id`, `brother_name`, `brother_occupation`, `sister_name`, `sister_occupation`, `income_father`, `income_mother`, `income_other`, `father_occ`, `mother_occ`, `forms`, `status`, `annual_income`, `date`, `award_id_id`, `student_id`, `bank_name`, `college_fee`, `college_name`, `constructed_area`, `father_occ_desc`, `four_wheeler`, `four_wheeler_desc`, `house`, `income_certificate`, `loan_amount`, `mother_occ_desc`, `plot_area`, `school_fee`, `school_name`, `two_wheeler`, `two_wheeler_desc`) VALUES
(4, 'yu', 'gg', 'hh', 'k', 12, 25, 58, 'Select', 'Select', 'SPACS_data_qDqPxbs.xlsx', 'Accept', 95, '2018-03-18', 8, '2015335', 'hhjn', 45, '23', 655, 'fhj', 5, '7', '', 'SPACS_data.xlsx', 56, 'jklh', 67, 466, 'nm', 8, '9');

-- --------------------------------------------------------

--
-- Table structure for table `meeting`
--

CREATE TABLE `meeting` (
  `id` int(11) NOT NULL,
  `venue` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `time` varchar(20) NOT NULL,
  `agenda` longtext NOT NULL,
  `minutes_file` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `notional_prize`
--

CREATE TABLE `notional_prize` (
  `id` int(11) NOT NULL,
  `spi` double NOT NULL,
  `cpi` double NOT NULL,
  `year` varchar(10) NOT NULL,
  `award_id_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `notional_prize`
--

INSERT INTO `notional_prize` (`id`, `spi`, `cpi`, `year`, `award_id_id`) VALUES
(1, 8.5, 8.5, 'UG1', 7);

-- --------------------------------------------------------

--
-- Table structure for table `previous_winner`
--

CREATE TABLE `previous_winner` (
  `id` int(11) NOT NULL,
  `year` int(11) NOT NULL,
  `award_id_id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `previous_winner`
--

INSERT INTO `previous_winner` (`id`, `year`, `award_id_id`, `student_id`) VALUES
(1, 2018, 2, '2015335'),
(2, 2018, 5, '2015335'),
(3, 2018, 8, '2015335'),
(4, 2017, 8, '2015335'),
(5, 2018, 8, '2015335'),
(6, 2018, 2, '2015335'),
(7, 2018, 2, '2015335'),
(8, 2018, 2, '2015335');

-- --------------------------------------------------------

--
-- Table structure for table `proficiency_dm`
--

CREATE TABLE `proficiency_dm` (
  `id` int(11) NOT NULL,
  `relevant_document` varchar(100) DEFAULT NULL,
  `title_name` varchar(30) DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `nearest_policestation` varchar(25) DEFAULT NULL,
  `nearest_railwaystation` varchar(25) DEFAULT NULL,
  `correspondence_address` varchar(100) DEFAULT NULL,
  `no_of_students` int(11) NOT NULL,
  `date` date NOT NULL,
  `award_id_id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `brief_description` longtext,
  `cse_percentage` int(11) DEFAULT NULL,
  `cse_topic` varchar(25) DEFAULT NULL,
  `design_percentage` int(11) DEFAULT NULL,
  `design_topic` varchar(25) DEFAULT NULL,
  `ece_percentage` int(11) DEFAULT NULL,
  `ece_topic` varchar(25) DEFAULT NULL,
  `financial_assistance` longtext,
  `grand_total` int(11) DEFAULT NULL,
  `justification` longtext,
  `mech_percentage` int(11) DEFAULT NULL,
  `mech_topic` varchar(25) DEFAULT NULL,
  `roll_no1` int(11) NOT NULL,
  `roll_no2` int(11) NOT NULL,
  `roll_no3` int(11) NOT NULL,
  `roll_no4` int(11) NOT NULL,
  `roll_no5` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `proficiency_dm`
--

INSERT INTO `proficiency_dm` (`id`, `relevant_document`, `title_name`, `status`, `nearest_policestation`, `nearest_railwaystation`, `correspondence_address`, `no_of_students`, `date`, `award_id_id`, `student_id`, `brief_description`, `cse_percentage`, `cse_topic`, `design_percentage`, `design_topic`, `ece_percentage`, `ece_topic`, `financial_assistance`, `grand_total`, `justification`, `mech_percentage`, `mech_topic`, `roll_no1`, `roll_no2`, `roll_no3`, `roll_no4`, `roll_no5`) VALUES
(1, 'Award_Catalogue_FSNF5jc.xlsx', 'sdgdsf', 'INOMPLETE', 'lak;sj', 'lkdsf', 'ldkf', 1, '2018-03-28', 10, '2015335', '22', 22, '2', 2, '2', 2, '22', NULL, 25, '2', 2, '22', 222, 2, 22, 22, 22);

-- --------------------------------------------------------

--
-- Table structure for table `release`
--

CREATE TABLE `release` (
  `id` int(11) NOT NULL,
  `startdate` date NOT NULL,
  `enddate` date NOT NULL,
  `remarks` longtext NOT NULL,
  `award` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `release`
--

INSERT INTO `release` (`id`, `startdate`, `enddate`, `remarks`, `award`) VALUES
(1, '2018-11-04', '2018-11-07', 'If u have any doubt contact me', 'Convocation Medals'),
(2, '2017-11-03', '2017-12-16', '', 'Convocation Medals'),
(3, '2017-11-03', '2017-12-16', '', 'Convocation Medals'),
(4, '2017-11-03', '2017-12-16', 'hi helo', 'Convocation Medals'),
(5, '2017-11-03', '2017-12-16', 'hi', 'Convocation Medals'),
(6, '2017-11-03', '2017-12-16', 'hi hello this is to tell that we have invited applications', 'Convocation Medals'),
(7, '2017-11-03', '2017-12-16', 'remarks\r\n', 'Convocation Medals'),
(8, '2017-11-03', '2017-12-16', 'hi', 'Convocation Medals'),
(9, '2017-11-03', '2017-12-16', 'hi ', 'Convocation Medals'),
(10, '2017-11-03', '2017-12-16', 'jhkjhk', 'Convocation Medals'),
(11, '2017-11-03', '2017-12-16', 'fj', 'Convocation Medals'),
(12, '2017-11-03', '2017-12-16', 'akdsfjl', 'Mcm Scholarship'),
(13, '2017-11-03', '2017-12-16', 'akdfj', 'Convocation Medals');

-- --------------------------------------------------------

--
-- Table structure for table `socialaccount_socialaccount`
--

CREATE TABLE `socialaccount_socialaccount` (
  `id` int(11) NOT NULL,
  `provider` varchar(30) NOT NULL,
  `uid` varchar(191) NOT NULL,
  `last_login` datetime(6) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `extra_data` longtext NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `socialaccount_socialapp`
--

CREATE TABLE `socialaccount_socialapp` (
  `id` int(11) NOT NULL,
  `provider` varchar(30) NOT NULL,
  `name` varchar(40) NOT NULL,
  `client_id` varchar(191) NOT NULL,
  `secret` varchar(191) NOT NULL,
  `key` varchar(191) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `socialaccount_socialapp_sites`
--

CREATE TABLE `socialaccount_socialapp_sites` (
  `id` int(11) NOT NULL,
  `socialapp_id` int(11) NOT NULL,
  `site_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `socialaccount_socialtoken`
--

CREATE TABLE `socialaccount_socialtoken` (
  `id` int(11) NOT NULL,
  `token` longtext NOT NULL,
  `token_secret` longtext NOT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `account_id` int(11) NOT NULL,
  `app_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `spi`
--

CREATE TABLE `spi` (
  `id` int(11) NOT NULL,
  `sem` int(11) NOT NULL,
  `spi` double NOT NULL,
  `student_id_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `student_attendance`
--

CREATE TABLE `student_attendance` (
  `id` int(11) NOT NULL,
  `attend` varchar(6) NOT NULL,
  `date` date NOT NULL,
  `course_id_id` int(11) NOT NULL,
  `student_id_id` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `timetable`
--

CREATE TABLE `timetable` (
  `id` int(11) NOT NULL,
  `upload_date` datetime(6) NOT NULL,
  `time_table` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `academic_information_student`
--
ALTER TABLE `academic_information_student`
  ADD PRIMARY KEY (`id_id`);

--
-- Indexes for table `account_emailaddress`
--
ALTER TABLE `account_emailaddress`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `account_emailaddress_user_id_2c513194_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `account_emailconfirmation`
--
ALTER TABLE `account_emailconfirmation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `key` (`key`),
  ADD KEY `account_emailconfirm_email_address_id_5b7f8c58_fk_account_e` (`email_address_id`);

--
-- Indexes for table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Indexes for table `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

--
-- Indexes for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `award_and_scholarship`
--
ALTER TABLE `award_and_scholarship`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `calendar`
--
ALTER TABLE `calendar`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `course`
--
ALTER TABLE `course`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `course_id` (`course_id`),
  ADD UNIQUE KEY `Course_course_id_course_name_sem_e9bbe6c5_uniq` (`course_id`,`course_name`,`sem`);

--
-- Indexes for table `director_gold`
--
ALTER TABLE `director_gold`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Director_gold_student_id_2bd0daec_fk_academic_` (`student_id`),
  ADD KEY `Director_gold_award_id_id_f10222b9_fk_Award_and_scholarship_id` (`award_id_id`);

--
-- Indexes for table `director_silver`
--
ALTER TABLE `director_silver`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Director_silver_award_id_id_4a0a4da5_fk_Award_and_scholarship_id` (`award_id_id`),
  ADD KEY `Director_silver_student_id_aed44080_fk_academic_` (`student_id`);

--
-- Indexes for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Indexes for table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- Indexes for table `django_site`
--
ALTER TABLE `django_site`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_site_domain_a2e37b91_uniq` (`domain`);

--
-- Indexes for table `exam_timetable`
--
ALTER TABLE `exam_timetable`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `globals_departmentinfo`
--
ALTER TABLE `globals_departmentinfo`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `globals_designation`
--
ALTER TABLE `globals_designation`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `globals_extrainfo`
--
ALTER TABLE `globals_extrainfo`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`),
  ADD KEY `globals_extrainfo_department_id_848d9717_fk_globals_d` (`department_id`);

--
-- Indexes for table `globals_faculty`
--
ALTER TABLE `globals_faculty`
  ADD PRIMARY KEY (`id_id`);

--
-- Indexes for table `globals_feedback`
--
ALTER TABLE `globals_feedback`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Indexes for table `globals_holdsdesignation`
--
ALTER TABLE `globals_holdsdesignation`
  ADD PRIMARY KEY (`id`),
  ADD KEY `globals_holdsdesigna_designation_id_074911c0_fk_globals_d` (`designation_id`),
  ADD KEY `globals_holdsdesignation_user_id_0816ffa6_fk_auth_user_id` (`user_id`),
  ADD KEY `globals_holdsdesignation_working_id_70883028_fk_auth_user_id` (`working_id`);

--
-- Indexes for table `globals_issue`
--
ALTER TABLE `globals_issue`
  ADD PRIMARY KEY (`id`),
  ADD KEY `globals_issue_user_id_98110616_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `globals_issueimage`
--
ALTER TABLE `globals_issueimage`
  ADD PRIMARY KEY (`id`),
  ADD KEY `globals_issueimage_user_id_be9b82a4_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `globals_issue_images`
--
ALTER TABLE `globals_issue_images`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `globals_issue_images_issue_id_issueimage_id_8a046f88_uniq` (`issue_id`,`issueimage_id`),
  ADD KEY `globals_issue_images_issueimage_id_0ed13bbe_fk_globals_i` (`issueimage_id`);

--
-- Indexes for table `globals_issue_support`
--
ALTER TABLE `globals_issue_support`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `globals_issue_support_issue_id_user_id_ccf999be_uniq` (`issue_id`,`user_id`),
  ADD KEY `globals_issue_support_user_id_db434ee4_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `globals_staff`
--
ALTER TABLE `globals_staff`
  ADD PRIMARY KEY (`id_id`);

--
-- Indexes for table `grades`
--
ALTER TABLE `grades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Grades_course_id_id_33a28f62_fk_Course_id` (`course_id_id`),
  ADD KEY `Grades_student_id_id_a6479b11_fk_academic_` (`student_id_id`);

--
-- Indexes for table `holiday`
--
ALTER TABLE `holiday`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `instructor`
--
ALTER TABLE `instructor`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `Instructor_course_id_id_instructor_id_id_1bb770d2_uniq` (`course_id_id`,`instructor_id_id`),
  ADD KEY `Instructor_instructor_id_id_49c97c28_fk_globals_extrainfo_id` (`instructor_id_id`);

--
-- Indexes for table `mcm`
--
ALTER TABLE `mcm`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Mcm_award_id_id_84bab89f_fk_Award_and_scholarship_id` (`award_id_id`),
  ADD KEY `Mcm_student_id_db5733e3_fk_academic_information_student_id_id` (`student_id`);

--
-- Indexes for table `meeting`
--
ALTER TABLE `meeting`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `notional_prize`
--
ALTER TABLE `notional_prize`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Notional_prize_award_id_id_529f43b9_fk_Award_and_scholarship_id` (`award_id_id`);

--
-- Indexes for table `previous_winner`
--
ALTER TABLE `previous_winner`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Previous_winner_award_id_id_62ccabe7_fk_Award_and_scholarship_id` (`award_id_id`),
  ADD KEY `Previous_winner_student_id_a5f38bc4_fk_academic_` (`student_id`);

--
-- Indexes for table `proficiency_dm`
--
ALTER TABLE `proficiency_dm`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Proficiency_dm_award_id_id_be7abc9f_fk_Award_and_scholarship_id` (`award_id_id`),
  ADD KEY `Proficiency_dm_student_id_c57558f6_fk_academic_` (`student_id`);

--
-- Indexes for table `release`
--
ALTER TABLE `release`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `socialaccount_socialaccount`
--
ALTER TABLE `socialaccount_socialaccount`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `socialaccount_socialaccount_provider_uid_fc810c6e_uniq` (`provider`,`uid`),
  ADD KEY `socialaccount_socialaccount_user_id_8146e70c_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `socialaccount_socialapp`
--
ALTER TABLE `socialaccount_socialapp`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `socialaccount_socialapp_sites`
--
ALTER TABLE `socialaccount_socialapp_sites`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `socialaccount_socialapp_sites_socialapp_id_site_id_71a9a768_uniq` (`socialapp_id`,`site_id`),
  ADD KEY `socialaccount_socialapp_sites_site_id_2579dee5_fk_django_site_id` (`site_id`);

--
-- Indexes for table `socialaccount_socialtoken`
--
ALTER TABLE `socialaccount_socialtoken`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq` (`app_id`,`account_id`),
  ADD KEY `socialaccount_social_account_id_951f210e_fk_socialacc` (`account_id`);

--
-- Indexes for table `spi`
--
ALTER TABLE `spi`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `Spi_student_id_id_sem_d19bf544_uniq` (`student_id_id`,`sem`);

--
-- Indexes for table `student_attendance`
--
ALTER TABLE `student_attendance`
  ADD PRIMARY KEY (`id`),
  ADD KEY `Student_attendance_course_id_id_25571805_fk_Course_id` (`course_id_id`),
  ADD KEY `Student_attendance_student_id_id_42adc818_fk_academic_` (`student_id_id`);

--
-- Indexes for table `timetable`
--
ALTER TABLE `timetable`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `account_emailaddress`
--
ALTER TABLE `account_emailaddress`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `account_emailconfirmation`
--
ALTER TABLE `account_emailconfirmation`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=334;

--
-- AUTO_INCREMENT for table `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `award_and_scholarship`
--
ALTER TABLE `award_and_scholarship`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `calendar`
--
ALTER TABLE `calendar`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `course`
--
ALTER TABLE `course`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `director_gold`
--
ALTER TABLE `director_gold`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `director_silver`
--
ALTER TABLE `director_silver`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- AUTO_INCREMENT for table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=112;

--
-- AUTO_INCREMENT for table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `django_site`
--
ALTER TABLE `django_site`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `exam_timetable`
--
ALTER TABLE `exam_timetable`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `globals_departmentinfo`
--
ALTER TABLE `globals_departmentinfo`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `globals_designation`
--
ALTER TABLE `globals_designation`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `globals_feedback`
--
ALTER TABLE `globals_feedback`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `globals_holdsdesignation`
--
ALTER TABLE `globals_holdsdesignation`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `globals_issue`
--
ALTER TABLE `globals_issue`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `globals_issueimage`
--
ALTER TABLE `globals_issueimage`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `globals_issue_images`
--
ALTER TABLE `globals_issue_images`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `globals_issue_support`
--
ALTER TABLE `globals_issue_support`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `grades`
--
ALTER TABLE `grades`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `holiday`
--
ALTER TABLE `holiday`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `instructor`
--
ALTER TABLE `instructor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `mcm`
--
ALTER TABLE `mcm`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `meeting`
--
ALTER TABLE `meeting`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `notional_prize`
--
ALTER TABLE `notional_prize`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `previous_winner`
--
ALTER TABLE `previous_winner`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `proficiency_dm`
--
ALTER TABLE `proficiency_dm`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `release`
--
ALTER TABLE `release`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `socialaccount_socialaccount`
--
ALTER TABLE `socialaccount_socialaccount`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `socialaccount_socialapp`
--
ALTER TABLE `socialaccount_socialapp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `socialaccount_socialapp_sites`
--
ALTER TABLE `socialaccount_socialapp_sites`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `socialaccount_socialtoken`
--
ALTER TABLE `socialaccount_socialtoken`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `spi`
--
ALTER TABLE `spi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `student_attendance`
--
ALTER TABLE `student_attendance`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `timetable`
--
ALTER TABLE `timetable`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `academic_information_student`
--
ALTER TABLE `academic_information_student`
  ADD CONSTRAINT `academic_information_id_id_04c54754_fk_globals_e` FOREIGN KEY (`id_id`) REFERENCES `globals_extrainfo` (`id`);

--
-- Constraints for table `account_emailaddress`
--
ALTER TABLE `account_emailaddress`
  ADD CONSTRAINT `account_emailaddress_user_id_2c513194_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `account_emailconfirmation`
--
ALTER TABLE `account_emailconfirmation`
  ADD CONSTRAINT `account_emailconfirm_email_address_id_5b7f8c58_fk_account_e` FOREIGN KEY (`email_address_id`) REFERENCES `account_emailaddress` (`id`);

--
-- Constraints for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Constraints for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Constraints for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `director_gold`
--
ALTER TABLE `director_gold`
  ADD CONSTRAINT `Director_gold_award_id_id_f10222b9_fk_Award_and_scholarship_id` FOREIGN KEY (`award_id_id`) REFERENCES `award_and_scholarship` (`id`),
  ADD CONSTRAINT `Director_gold_student_id_2bd0daec_fk_academic_` FOREIGN KEY (`student_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `director_silver`
--
ALTER TABLE `director_silver`
  ADD CONSTRAINT `Director_silver_award_id_id_4a0a4da5_fk_Award_and_scholarship_id` FOREIGN KEY (`award_id_id`) REFERENCES `award_and_scholarship` (`id`),
  ADD CONSTRAINT `Director_silver_student_id_aed44080_fk_academic_` FOREIGN KEY (`student_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_extrainfo`
--
ALTER TABLE `globals_extrainfo`
  ADD CONSTRAINT `globals_extrainfo_department_id_848d9717_fk_globals_d` FOREIGN KEY (`department_id`) REFERENCES `globals_departmentinfo` (`id`),
  ADD CONSTRAINT `globals_extrainfo_user_id_eda09c50_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_faculty`
--
ALTER TABLE `globals_faculty`
  ADD CONSTRAINT `globals_faculty_id_id_0fd6c5e4_fk_globals_extrainfo_id` FOREIGN KEY (`id_id`) REFERENCES `globals_extrainfo` (`id`);

--
-- Constraints for table `globals_feedback`
--
ALTER TABLE `globals_feedback`
  ADD CONSTRAINT `globals_feedback_user_id_3aa92ccc_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_holdsdesignation`
--
ALTER TABLE `globals_holdsdesignation`
  ADD CONSTRAINT `globals_holdsdesigna_designation_id_074911c0_fk_globals_d` FOREIGN KEY (`designation_id`) REFERENCES `globals_designation` (`id`),
  ADD CONSTRAINT `globals_holdsdesignation_user_id_0816ffa6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `globals_holdsdesignation_working_id_70883028_fk_auth_user_id` FOREIGN KEY (`working_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_issue`
--
ALTER TABLE `globals_issue`
  ADD CONSTRAINT `globals_issue_user_id_98110616_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_issueimage`
--
ALTER TABLE `globals_issueimage`
  ADD CONSTRAINT `globals_issueimage_user_id_be9b82a4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_issue_images`
--
ALTER TABLE `globals_issue_images`
  ADD CONSTRAINT `globals_issue_images_issue_id_a7df473d_fk_globals_issue_id` FOREIGN KEY (`issue_id`) REFERENCES `globals_issue` (`id`),
  ADD CONSTRAINT `globals_issue_images_issueimage_id_0ed13bbe_fk_globals_i` FOREIGN KEY (`issueimage_id`) REFERENCES `globals_issueimage` (`id`);

--
-- Constraints for table `globals_issue_support`
--
ALTER TABLE `globals_issue_support`
  ADD CONSTRAINT `globals_issue_support_issue_id_2ed52d1d_fk_globals_issue_id` FOREIGN KEY (`issue_id`) REFERENCES `globals_issue` (`id`),
  ADD CONSTRAINT `globals_issue_support_user_id_db434ee4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `globals_staff`
--
ALTER TABLE `globals_staff`
  ADD CONSTRAINT `globals_staff_id_id_41d590e6_fk_globals_extrainfo_id` FOREIGN KEY (`id_id`) REFERENCES `globals_extrainfo` (`id`);

--
-- Constraints for table `grades`
--
ALTER TABLE `grades`
  ADD CONSTRAINT `Grades_course_id_id_33a28f62_fk_Course_id` FOREIGN KEY (`course_id_id`) REFERENCES `course` (`id`),
  ADD CONSTRAINT `Grades_student_id_id_a6479b11_fk_academic_` FOREIGN KEY (`student_id_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `instructor`
--
ALTER TABLE `instructor`
  ADD CONSTRAINT `Instructor_course_id_id_c82a17fd_fk_Course_id` FOREIGN KEY (`course_id_id`) REFERENCES `course` (`id`),
  ADD CONSTRAINT `Instructor_instructor_id_id_49c97c28_fk_globals_extrainfo_id` FOREIGN KEY (`instructor_id_id`) REFERENCES `globals_extrainfo` (`id`);

--
-- Constraints for table `mcm`
--
ALTER TABLE `mcm`
  ADD CONSTRAINT `Mcm_award_id_id_84bab89f_fk_Award_and_scholarship_id` FOREIGN KEY (`award_id_id`) REFERENCES `award_and_scholarship` (`id`),
  ADD CONSTRAINT `Mcm_student_id_db5733e3_fk_academic_information_student_id_id` FOREIGN KEY (`student_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `notional_prize`
--
ALTER TABLE `notional_prize`
  ADD CONSTRAINT `Notional_prize_award_id_id_529f43b9_fk_Award_and_scholarship_id` FOREIGN KEY (`award_id_id`) REFERENCES `award_and_scholarship` (`id`);

--
-- Constraints for table `previous_winner`
--
ALTER TABLE `previous_winner`
  ADD CONSTRAINT `Previous_winner_award_id_id_62ccabe7_fk_Award_and_scholarship_id` FOREIGN KEY (`award_id_id`) REFERENCES `award_and_scholarship` (`id`),
  ADD CONSTRAINT `Previous_winner_student_id_a5f38bc4_fk_academic_` FOREIGN KEY (`student_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `proficiency_dm`
--
ALTER TABLE `proficiency_dm`
  ADD CONSTRAINT `Proficiency_dm_award_id_id_be7abc9f_fk_Award_and_scholarship_id` FOREIGN KEY (`award_id_id`) REFERENCES `award_and_scholarship` (`id`),
  ADD CONSTRAINT `Proficiency_dm_student_id_c57558f6_fk_academic_` FOREIGN KEY (`student_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `socialaccount_socialaccount`
--
ALTER TABLE `socialaccount_socialaccount`
  ADD CONSTRAINT `socialaccount_socialaccount_user_id_8146e70c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `socialaccount_socialapp_sites`
--
ALTER TABLE `socialaccount_socialapp_sites`
  ADD CONSTRAINT `socialaccount_social_socialapp_id_97fb6e7d_fk_socialacc` FOREIGN KEY (`socialapp_id`) REFERENCES `socialaccount_socialapp` (`id`),
  ADD CONSTRAINT `socialaccount_socialapp_sites_site_id_2579dee5_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`);

--
-- Constraints for table `socialaccount_socialtoken`
--
ALTER TABLE `socialaccount_socialtoken`
  ADD CONSTRAINT `socialaccount_social_account_id_951f210e_fk_socialacc` FOREIGN KEY (`account_id`) REFERENCES `socialaccount_socialaccount` (`id`),
  ADD CONSTRAINT `socialaccount_social_app_id_636a42d7_fk_socialacc` FOREIGN KEY (`app_id`) REFERENCES `socialaccount_socialapp` (`id`);

--
-- Constraints for table `spi`
--
ALTER TABLE `spi`
  ADD CONSTRAINT `Spi_student_id_id_30d58f0b_fk_academic_information_student_id_id` FOREIGN KEY (`student_id_id`) REFERENCES `academic_information_student` (`id_id`);

--
-- Constraints for table `student_attendance`
--
ALTER TABLE `student_attendance`
  ADD CONSTRAINT `Student_attendance_course_id_id_25571805_fk_Course_id` FOREIGN KEY (`course_id_id`) REFERENCES `course` (`id`),
  ADD CONSTRAINT `Student_attendance_student_id_id_42adc818_fk_academic_` FOREIGN KEY (`student_id_id`) REFERENCES `academic_information_student` (`id_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
