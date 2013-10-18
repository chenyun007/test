
    /************************************************
    -- Author:Azik
    -- Description:加载管理费收入，分保有收入与新增收入
    ************************************************/
   
    v_num_commit_rows INT := 10000;
    v_num_commit_cnt  INT := 0;

    v_num_sk_confirmdate       NUMBER(8) := 0;
    v_num_sk_dept              NUMBER(12) := -1;
    v_num_sk_emp               NUMBER(12) := -1;
    v_str_bk_fundcode          VARCHAR2(10) := 'XXXXXX';
    v_num_sk_agency            NUMBER(12) := -1;
    v_num_redeem_acc_month     NUMBER(32, 6) := 0;
    v_num_redeem_acc_quarter   NUMBER(32, 6) := 0;
    v_num_redeem_acc_year      NUMBER(32, 6) := 0;
    v_num_shares_init_month    NUMBER(17, 2) := 0;
    v_num_shares_init_quarter  NUMBER(17, 2) := 0;
    v_num_shares_init_year     NUMBER(17, 2) := 0;
    v_num_purchase_acc_month   NUMBER(32, 6) := 0;
    v_num_purchase_acc_quarter NUMBER(32, 6) := 0;
    v_num_purchase_acc_year    NUMBER(32, 6) := 0;
    v_num_redeemfare           NUMBER(12, 2) := 0;
    v_num_fst_day_of_month     NUMBER(8) := 0;
    v_num_fst_day_of_quarter   NUMBER(8) := 0;
    v_num_fst_day_of_year      NUMBER(8) := 0;
    v_num_effective_to         NUMBER(8) := 0;
    v_num_quarter_cur          NUMBER(8) := 0;
    v_num_quarter_pre          NUMBER(8) := 0;
    v_num_year_cur             NUMBER(8) := 0;
    v_num_year_pre             NUMBER(8) := 0;
    v_str_agencyno             VARCHAR2(10) := 'XXX';

  BEGIN
   
    truncate table TMP_FACT_EMP_INCOME_D_1;
    INSERT INTO TMP_FACT_EMP_INCOME_D_1
      (SK_CONFIRMDATE, BK_FUNDCODE, SK_AGENCY, SK_DEPT, SK_EMP, AGENCYNO)
      SELECT MAX(FT.SK_CONFIRMDATE) AS SK_CONFIRMDATE,
             FT.BK_FUNDCODE,
             FT.SK_AGENCY,
             FT.SK_DEPT,
             FT.SK_EMP,
             FT.AGENCYNO
        FROM FACT_EMP_INCOME_D FT
       WHERE FT.SK_CONFIRMDATE < :startdate
       GROUP BY FT.BK_FUNDCODE,
                FT.SK_AGENCY,
                FT.SK_DEPT,
                FT.SK_EMP,
                FT.AGENCYNO;
	 truncate table TMP_FACT_EMP_INCOME_D_2;
    INSERT INTO TMP_FACT_EMP_INCOME_D_2
      (SK_CONFIRMDATE,
       SK_DEPT,
       SK_EMP,
       BK_FUNDCODE,
       SK_AGENCY,
       REDEEM_ACC_MONTH,
       REDEEM_ACC_QUARTER,
       REDEEM_ACC_YEAR,
       SHARES_INIT_MONTH,
       SHARES_INIT_QUARTER,
       SHARES_INIT_YEAR,
       PURCHASE_ACC_MONTH,
       PURCHASE_ACC_QUARTER,
       PURCHASE_ACC_YEAR,
       REDEEMFARE,
       AGENCYNO)
      SELECT SK_CONFIRMDATE,
             SK_DEPT,
             SK_EMP,
             BK_FUNDCODE,
             SK_AGENCY,
             REDEEM_ACC_MONTH,
             REDEEM_ACC_QUARTER,
             REDEEM_ACC_YEAR,
             SHARES_INIT_MONTH,
             SHARES_INIT_QUARTER,
             SHARES_INIT_YEAR,
             PURCHASE_ACC_MONTH,
             PURCHASE_ACC_QUARTER,
             PURCHASE_ACC_YEAR,
             REDEEMFARE,
             AGENCYNO
        FROM FACT_EMP_INCOME_D FT
       WHERE EXISTS (SELECT 1
                FROM TMP_FACT_EMP_INCOME_D_1 TMP
               WHERE TMP.SK_CONFIRMDATE = FT.SK_CONFIRMDATE
                 AND TMP.BK_FUNDCODE = FT.BK_FUNDCODE
                 AND TMP.SK_AGENCY = FT.SK_AGENCY
                 AND TMP.SK_DEPT = FT.SK_DEPT
                 AND TMP.SK_EMP = FT.SK_EMP
                 AND TMP.AGENCYNO = FT.AGENCYNO);
    COMMIT;

    truncate table TMP_FACT_EMP_INCOME_D_3;
    INSERT INTO TMP_FACT_EMP_INCOME_D_3
      (SK_CONFIRMDATE,
       BK_FUNDCODE,
       SK_AGENCY,
       SK_DEPT,
       SK_EMP,
       PURCHASE_SHARES,
       REDEEM_SHARES,
       REDEEMFARE,
       AGENCYNO)
      SELECT FT.SK_CONFIRMDATE,
             FT.BK_FUNDCODE,
             FT.SK_AGENCY,
             NVL(DMDPAG.SK_DEPT, -1) AS SK_DEPT,
             NVL(DMAGCH.SK_EMPLOYEE, -1) AS SK_EMP,
             SUM(CASE
                   WHEN FT.BK_TRADETYPE in ('139',
                                            '134',
                                            '143',
                                            '130',
                                            '137',
                                            'T14',
                                            '198',
                                            '144',
                                            '122',
                                            '127') THEN
                    FT.SHARES * NVL(DMAGCH.RATIO, 1)
                   ELSE
                    0
                 END) AS PURCHASE_SHARES,
             SUM(CASE
                   WHEN FT.BK_TRADETYPE IN ('163',
                                            '195',
                                            '135',
                                            '150',
                                            '151',
                                            '138',
                                            'T15',
                                            '199',
                                            '145',
                                            '142',
                                            '124',
                                            '128',
                                            '125') THEN
                    FT.SHARES * NVL(DMAGCH.RATIO, 1)
                   ELSE
                    0
                 END) AS REDEEM_SHARES,
             SUM(CASE
                   WHEN FT.BK_TRADETYPE IN ('124', '142') THEN
                    FT.REGISTFARE * NVL(DMAGCH.RATIO, 1)
                   ELSE
                    0
                 END) AS REDEEMFARE,
             AGENCYNO
        FROM FACT_TRANSACTION_DETAIL FT
        LEFT JOIN DIM_AGENCYCHNLMNGR_RELA DMAGCH
          ON (FT.SK_AGENCY = DMAGCH.SK_AGENCY AND
             FT.SK_CONFIRMDATE >= DMAGCH.EFFECTIVE_FROM AND
             FT.SK_CONFIRMDATE < DMAGCH.EFFECTIVE_TO)
        LEFT JOIN DIM_DEPTAGENCY_RELA DMDPAG
          ON (DMDPAG.SK_AGENCY = FT.SK_AGENCY AND
             FT.SK_CONFIRMDATE >= DMDPAG.EFFECTIVE_FROM AND
             FT.SK_CONFIRMDATE < DMDPAG.EFFECTIVE_TO)
       WHERE FT.TRANSTATUS = '成功'
         AND FT.BK_TRADETYPE IN ('139',
                                 '134',
                                 '143',
                                 '130',
                                 '137',
                                 'T14',
                                 '198',
                                 '144',
                                 '122',
                                 '127', --导致份额增加的交易
                                 '163',
                                 '195',
                                 '135',
                                 '150',
                                 '151',
                                 '138',
                                 'T15',
                                 '199',
                                 '145',
                                 '142',
                                 '124',
                                 '128',
                                 '125' --导致份额减少的交易
                                 )
         AND FT.SK_CONFIRMDATE BETWEEN :startdate AND :enddate
       GROUP BY FT.SK_CONFIRMDATE,
                FT.BK_FUNDCODE,
                FT.SK_AGENCY,
                NVL(DMAGCH.SK_EMPLOYEE, -1),
                NVL(DMDPAG.SK_DEPT, -1),
                AGENCYNO;
    COMMIT;

    truncate table TMP_FACT_EMP_INCOME_D_4;
    INSERT INTO TMP_FACT_EMP_INCOME_D_4
      (SK_CONFIRMDATE,
       FST_DAY_OF_MONTH,
       FST_DAY_OF_QUARTER,
       FST_DAY_OF_YEAR)
      SELECT DMTM.SK_DATE AS SK_CONFIRMDATE,
             FLOOR(DMTM.SK_DATE / 100) * 100 + 1 AS FST_DAY_OF_MONTH,
             (SELECT MIN(T.SK_DATE)
                FROM DIM_TIME T
               WHERE T.GREQUARTER = DMTM.GREQUARTER
                 AND T.GREYEAR = DMTM.GREYEAR) AS FST_DAY_OF_QUARTER,
             FLOOR(DMTM.SK_DATE / 10000) * 10000 + 101 AS FST_DAY_OF_YEAR
        FROM DIM_TIME DMTM
       WHERE DMTM.SK_DATE BETWEEN :startdate AND :enddate;
    COMMIT;

    truncate table TMP_FACT_EMP_INCOME_D_5;
    INSERT INTO TMP_FACT_EMP_INCOME_D_5
      (SK_CONFIRMDATE,
       BK_FUNDCODE,
       SK_AGENCY,
       SK_DEPT,
       SK_EMP,
       SHARES_INIT,
       AGENCYNO)
      SELECT DMTM.SK_CONFIRMDATE,
             FT.BK_FUNDCODE,
             FT.SK_AGENCY,
             NVL(DMDPAG.SK_DEPT, -1) AS SK_DEPT,
             NVL(DMAGCH.SK_EMPLOYEE, -1) AS SK_EMP,
             SUM(FT.SHARES * NVL(DMAGCH.RATIO, 1)) AS SHARES_INIT,
             FT.AGENCYNO
        FROM FACT_FUNDBAL_DETAIL FT
       INNER JOIN (SELECT FST_DAY_OF_MONTH AS SK_CONFIRMDATE
                     FROM TMP_FACT_EMP_INCOME_D_4
                   UNION
                   SELECT FST_DAY_OF_QUARTER AS SK_CONFIRMDATE
                     FROM TMP_FACT_EMP_INCOME_D_4
                   UNION
                   SELECT FST_DAY_OF_YEAR AS SK_CONFIRMDATE
                     FROM TMP_FACT_EMP_INCOME_D_4) DMTM
          ON (DMTM.SK_CONFIRMDATE >= FT.EFFECTIVE_FROM AND
             DMTM.SK_CONFIRMDATE < FT.EFFECTIVE_TO)
        LEFT JOIN DIM_AGENCYCHNLMNGR_RELA DMAGCH
          ON (FT.SK_AGENCY = DMAGCH.SK_AGENCY AND
             DMTM.SK_CONFIRMDATE >= DMAGCH.EFFECTIVE_FROM AND
             DMTM.SK_CONFIRMDATE < DMAGCH.EFFECTIVE_TO)
        LEFT JOIN DIM_DEPTAGENCY_RELA DMDPAG
          ON (DMDPAG.SK_AGENCY = FT.SK_AGENCY AND
             DMTM.SK_CONFIRMDATE >= DMDPAG.EFFECTIVE_FROM AND
             DMTM.SK_CONFIRMDATE < DMDPAG.EFFECTIVE_TO)
       GROUP BY DMTM.SK_CONFIRMDATE,
                FT.BK_FUNDCODE,
                FT.SK_AGENCY,
                NVL(DMAGCH.SK_EMPLOYEE, -1),
                NVL(DMDPAG.SK_DEPT, -1),
                FT.AGENCYNO;
    COMMIT;

    truncate table TMP_FACT_EMP_INCOME_D_6;
    FOR TMP_CUR IN (SELECT T2.sk_confirmdate,
                           T2.sk_dept,
                           T2.sk_emp,
                           T2.bk_fundcode,
                           T2.sk_agency,
                           T2.redeem_acc_month,
                           T2.redeem_acc_quarter,
                           T2.redeem_acc_year,
                           T2.shares_init_month,
                           T2.shares_init_quarter,
                           T2.shares_init_year,
                           T2.purchase_acc_month,
                           T2.purchase_acc_quarter,
                           T2.purchase_acc_year,
                           T2.redeemfare,
                           T4.FST_DAY_OF_MONTH,
                           T4.FST_DAY_OF_QUARTER,
                           T4.FST_DAY_OF_YEAR,
                           T2.AGENCYNO
                      FROM TMP_fact_emp_income_d_2 T2
                      LEFT JOIN TMP_FACT_EMP_INCOME_D_4 T4
                        ON (T2.SK_CONFIRMDATE = T4.SK_CONFIRMDATE)
                    UNION ALL
                    select sk_confirmdate,
                           sk_dept,
                           sk_emp,
                           bk_fundcode,
                           sk_agency,
                           sum(redeem_acc_month) as redeem_acc_month,
                           sum(redeem_acc_quarter) as redeem_acc_quarter,
                           sum(redeem_acc_year) as redeem_acc_year,
                           sum(shares_init_month) as shares_init_month,
                           sum(shares_init_quarter) as shares_init_quarter,
                           sum(shares_init_year) as shares_init_year,
                           sum(purchase_acc_month) as purchase_acc_month,
                           sum(purchase_acc_quarter) as purchase_acc_quarter,
                           sum(purchase_acc_year) as purchase_acc_year,
                           sum(redeemfare) as redeemfare,
                           FST_DAY_OF_MONTH,
                           FST_DAY_OF_QUARTER,
                           FST_DAY_OF_YEAR,
                           AGENCYNO
                      from (SELECT T3.sk_confirmdate,
                                   T3.sk_dept,
                                   T3.sk_emp,
                                   T3.bk_fundcode,
                                   T3.sk_agency,
                                   T3.REDEEM_SHARES      AS redeem_acc_month,
                                   T3.REDEEM_SHARES      AS redeem_acc_quarter,
                                   T3.REDEEM_SHARES      AS redeem_acc_year,
                                   0                     AS shares_init_month,
                                   0                     AS shares_init_quarter,
                                   0                     AS shares_init_year,
                                   T3.PURCHASE_SHARES    AS purchase_acc_month,
                                   T3.PURCHASE_SHARES    AS purchase_acc_quarter,
                                   T3.PURCHASE_SHARES    AS purchase_acc_year,
                                   T3.REDEEMFARE         AS redeemfare,
                                   T4.FST_DAY_OF_MONTH,
                                   T4.FST_DAY_OF_QUARTER,
                                   T4.FST_DAY_OF_YEAR,
                                   T3.AGENCYNO
                              FROM TMP_fact_emp_income_d_3 T3
                              LEFT JOIN TMP_FACT_EMP_INCOME_D_4 T4
                                ON (T3.SK_CONFIRMDATE = T4.SK_CONFIRMDATE)
                            union all
                            SELECT T4.sk_confirmdate,
                                   T51.sk_dept,
                                   T51.sk_emp,
                                   T51.bk_fundcode,
                                   T51.sk_agency,
                                   0                     AS redeem_acc_month,
                                   0                     AS redeem_acc_quarter,
                                   0                     AS redeem_acc_year,
                                   T51.SHARES_INIT       AS shares_init_month,
                                   0                     AS shares_init_quarter,
                                   0                     AS shares_init_year,
                                   0                     AS purchase_acc_month,
                                   0                     AS purchase_acc_quarter,
                                   0                     AS purchase_acc_year,
                                   0                     AS redeemfare,
                                   T4.FST_DAY_OF_MONTH,
                                   T4.FST_DAY_OF_QUARTER,
                                   T4.FST_DAY_OF_YEAR,
                                   T51.AGENCYNO
                              FROM TMP_FACT_EMP_INCOME_D_4 T4
                              LEFT JOIN TMP_FACT_EMP_INCOME_D_5 T51
                                ON (T4.FST_DAY_OF_MONTH = T51.SK_CONFIRMDATE)
                            union all
                            SELECT T4.sk_confirmdate,
                                   T52.sk_dept,
                                   T52.sk_emp,
                                   T52.bk_fundcode,
                                   T52.sk_agency,
                                   0                     AS redeem_acc_month,
                                   0                     AS redeem_acc_quarter,
                                   0                     AS redeem_acc_year,
                                   0                     AS shares_init_month,
                                   T52.SHARES_INIT       AS shares_init_quarter,
                                   0                     AS shares_init_year,
                                   0                     AS purchase_acc_month,
                                   0                     AS purchase_acc_quarter,
                                   0                     AS purchase_acc_year,
                                   0                     AS redeemfare,
                                   T4.FST_DAY_OF_MONTH,
                                   T4.FST_DAY_OF_QUARTER,
                                   T4.FST_DAY_OF_YEAR,
                                   T52.AGENCYNO
                              FROM TMP_FACT_EMP_INCOME_D_4 T4
                              LEFT JOIN TMP_FACT_EMP_INCOME_D_5 T52
                                ON (T4.FST_DAY_OF_QUARTER =
                                   T52.SK_CONFIRMDATE)
                            union all
                            SELECT T4.sk_confirmdate,
                                   T53.sk_dept,
                                   T53.sk_emp,
                                   T53.bk_fundcode,
                                   T53.sk_agency,
                                   0                     AS redeem_acc_month,
                                   0                     AS redeem_acc_quarter,
                                   0                     AS redeem_acc_year,
                                   0                     AS shares_init_month,
                                   0                     AS shares_init_quarter,
                                   T53.SHARES_INIT       AS shares_init_year,
                                   0                     AS purchase_acc_month,
                                   0                     AS purchase_acc_quarter,
                                   0                     AS purchase_acc_year,
                                   0                     AS redeemfare,
                                   T4.FST_DAY_OF_MONTH,
                                   T4.FST_DAY_OF_QUARTER,
                                   T4.FST_DAY_OF_YEAR,
                                   T53.AGENCYNO
                              FROM TMP_FACT_EMP_INCOME_D_4 T4
                              LEFT JOIN TMP_FACT_EMP_INCOME_D_5 T53
                                ON (T4.FST_DAY_OF_YEAR = T53.SK_CONFIRMDATE)) t
                     group by sk_confirmdate,
                              sk_dept,
                              sk_emp,
                              bk_fundcode,
                              sk_agency,
                              FST_DAY_OF_MONTH,
                              FST_DAY_OF_QUARTER,
                              FST_DAY_OF_YEAR,
                              AGENCYNO
                     ORDER BY SK_DEPT,
                              SK_EMP,
                              BK_FUNDCODE,
                              SK_AGENCY,
                              SK_CONFIRMDATE) LOOP
      IF TMP_CUR.SK_DEPT = v_num_sk_dept AND TMP_CUR.SK_EMP = v_num_sk_emp AND
         TMP_CUR.BK_FUNDCODE = v_str_bk_fundcode AND
         TMP_CUR.SK_AGENCY = v_num_sk_agency AND
         TMP_CUR.AGENCYNO = v_str_agencyno THEN
        INSERT INTO TMP_fact_emp_income_d_6
          (sk_confirmdate,
           sk_dept,
           sk_emp,
           bk_fundcode,
           sk_agency,
           redeem_acc_month,
           redeem_acc_quarter,
           redeem_acc_year,
           shares_init_month,
           shares_init_quarter,
           shares_init_year,
           purchase_acc_month,
           purchase_acc_quarter,
           purchase_acc_year,
           redeemfare,
           PURCHASE_SHARES,
           REDEEM_SHARES,
           AGENCYNO)
        VALUES
          (TMP_CUR.SK_CONFIRMDATE,
           TMP_CUR.SK_DEPT,
           TMP_CUR.SK_EMP,
           TMP_CUR.BK_FUNDCODE,
           TMP_CUR.SK_AGENCY,
           (CASE
             WHEN TMP_CUR.FST_DAY_OF_MONTH = v_num_fst_day_of_month THEN
              TMP_CUR.REDEEM_ACC_MONTH + v_num_redeem_acc_month
             ELSE
              TMP_CUR.REDEEM_ACC_MONTH
           END),
           (CASE
             WHEN TMP_CUR.FST_DAY_OF_QUARTER = v_num_fst_day_of_quarter THEN
              TMP_CUR.REDEEM_ACC_QUARTER + v_num_redeem_acc_quarter
             ELSE
              TMP_CUR.REDEEM_ACC_QUARTER
           END),
           (CASE
             WHEN TMP_CUR.FST_DAY_OF_YEAR = v_num_fst_day_of_year THEN
              TMP_CUR.REDEEM_ACC_YEAR + v_num_redeem_acc_year
             ELSE
              TMP_CUR.REDEEM_ACC_YEAR
           END),
           TMP_CUR.SHARES_INIT_MONTH,
           TMP_CUR.SHARES_INIT_QUARTER,
           TMP_CUR.SHARES_INIT_YEAR,
           (CASE
             WHEN TMP_CUR.FST_DAY_OF_MONTH = v_num_fst_day_of_month THEN
              TMP_CUR.PURCHASE_ACC_MONTH + v_num_purchase_acc_month
             ELSE
              TMP_CUR.PURCHASE_ACC_MONTH
           END),
           (CASE
             WHEN TMP_CUR.FST_DAY_OF_QUARTER = v_num_fst_day_of_quarter THEN
              TMP_CUR.PURCHASE_ACC_QUARTER + v_num_PURCHASE_acc_quarter
             ELSE
              TMP_CUR.PURCHASE_ACC_QUARTER
           END),
           (CASE
             WHEN TMP_CUR.FST_DAY_OF_YEAR = v_num_fst_day_of_year THEN
              TMP_CUR.PURCHASE_ACC_YEAR + v_num_PURCHASE_acc_year
             ELSE
              TMP_CUR.PURCHASE_ACC_YEAR
           END),
           TMP_CUR.REDEEMFARE,
           TMP_CUR.PURCHASE_ACC_MONTH,
           TMP_CUR.REDEEM_ACC_MONTH,
           TMP_CUR.AGENCYNO);
        v_num_sk_confirmdate       := TMP_CUR.SK_CONFIRMDATE;
        v_num_sk_dept              := TMP_CUR.SK_DEPT;
        v_num_sk_emp               := TMP_CUR.SK_EMP;
        v_str_bk_fundcode          := TMP_CUR.BK_FUNDCODE;
        v_num_sk_agency            := TMP_CUR.SK_AGENCY;
        v_num_redeem_acc_month := (CASE
                                    WHEN TMP_CUR.FST_DAY_OF_MONTH =
                                         v_num_fst_day_of_month THEN
                                     TMP_CUR.REDEEM_ACC_MONTH +
                                     v_num_redeem_acc_month
                                    ELSE
                                     TMP_CUR.REDEEM_ACC_MONTH
                                  END);
        v_num_redeem_acc_quarter := (CASE
                                      WHEN TMP_CUR.FST_DAY_OF_QUARTER =
                                           v_num_fst_day_of_quarter THEN
                                       TMP_CUR.REDEEM_ACC_QUARTER +
                                       v_num_redeem_acc_quarter
                                      ELSE
                                       TMP_CUR.REDEEM_ACC_QUARTER
                                    END);
        v_num_redeem_acc_year := (CASE
                                   WHEN TMP_CUR.FST_DAY_OF_YEAR =
                                        v_num_fst_day_of_year THEN
                                    TMP_CUR.REDEEM_ACC_YEAR +
                                    v_num_redeem_acc_year
                                   ELSE
                                    TMP_CUR.REDEEM_ACC_YEAR
                                 END);
        v_num_shares_init_month    := TMP_CUR.SHARES_INIT_MONTH;
        v_num_shares_init_quarter  := TMP_CUR.SHARES_INIT_QUARTER;
        v_num_shares_init_year     := TMP_CUR.SHARES_INIT_YEAR;
        v_num_purchase_acc_month := (CASE
                                      WHEN TMP_CUR.FST_DAY_OF_MONTH =
                                           v_num_fst_day_of_month THEN
                                       TMP_CUR.PURCHASE_ACC_MONTH +
                                       v_num_purchase_acc_month
                                      ELSE
                                       TMP_CUR.PURCHASE_ACC_MONTH
                                    END);
        v_num_purchase_acc_quarter := (CASE
                                        WHEN TMP_CUR.FST_DAY_OF_QUARTER =
                                             v_num_fst_day_of_quarter THEN
                                         TMP_CUR.PURCHASE_ACC_QUARTER +
                                         v_num_PURCHASE_acc_quarter
                                        ELSE
                                         TMP_CUR.PURCHASE_ACC_QUARTER
                                      END);
        v_num_purchase_acc_year := (CASE
                                     WHEN TMP_CUR.FST_DAY_OF_YEAR =
                                          v_num_fst_day_of_year THEN
                                      TMP_CUR.PURCHASE_ACC_YEAR +
                                      v_num_PURCHASE_acc_year
                                     ELSE
                                      TMP_CUR.PURCHASE_ACC_YEAR
                                   END);
        v_num_redeemfare           := TMP_CUR.REDEEMFARE;
        v_num_fst_day_of_month     := TMP_CUR.FST_DAY_OF_MONTH;
        v_num_fst_day_of_quarter   := TMP_CUR.FST_DAY_OF_QUARTER;
        v_num_fst_day_of_year      := TMP_CUR.FST_DAY_OF_YEAR;
        v_str_agencyno             := TMP_CUR.AGENCYNO;
      ELSE
        INSERT INTO TMP_fact_emp_income_d_6
          (sk_confirmdate,
           sk_dept,
           sk_emp,
           bk_fundcode,
           sk_agency,
           redeem_acc_month,
           redeem_acc_quarter,
           redeem_acc_year,
           shares_init_month,
           shares_init_quarter,
           shares_init_year,
           purchase_acc_month,
           purchase_acc_quarter,
           purchase_acc_year,
           redeemfare,
           PURCHASE_SHARES,
           REDEEM_SHARES,
           AGENCYNO)
        VALUES
          (TMP_CUR.sk_confirmdate,
           TMP_CUR.sk_dept,
           TMP_CUR.sk_emp,
           TMP_CUR.bk_fundcode,
           TMP_CUR.sk_agency,
           TMP_CUR.redeem_acc_month,
           TMP_CUR.redeem_acc_quarter,
           TMP_CUR.redeem_acc_year,
           TMP_CUR.shares_init_month,
           TMP_CUR.shares_init_quarter,
           TMP_CUR.shares_init_year,
           TMP_CUR.purchase_acc_month,
           TMP_CUR.purchase_acc_quarter,
           TMP_CUR.purchase_acc_year,
           TMP_CUR.redeemfare,
           TMP_CUR.PURCHASE_ACC_MONTH,
           TMP_CUR.REDEEM_ACC_MONTH,
           TMP_CUR.AGENCYNO);
        v_num_sk_confirmdate       := TMP_CUR.SK_CONFIRMDATE;
        v_num_sk_dept              := TMP_CUR.SK_DEPT;
        v_num_sk_emp               := TMP_CUR.SK_EMP;
        v_str_bk_fundcode          := TMP_CUR.BK_FUNDCODE;
        v_num_sk_agency            := TMP_CUR.SK_AGENCY;
        v_num_redeem_acc_month     := TMP_CUR.REDEEM_ACC_MONTH;
        v_num_redeem_acc_quarter   := TMP_CUR.REDEEM_ACC_QUARTER;
        v_num_redeem_acc_year      := TMP_CUR.REDEEM_ACC_YEAR;
        v_num_shares_init_month    := TMP_CUR.SHARES_INIT_MONTH;
        v_num_shares_init_quarter  := TMP_CUR.SHARES_INIT_QUARTER;
        v_num_shares_init_year     := TMP_CUR.SHARES_INIT_YEAR;
        v_num_purchase_acc_month   := TMP_CUR.PURCHASE_ACC_MONTH;
        v_num_purchase_acc_quarter := TMP_CUR.PURCHASE_ACC_QUARTER;
        v_num_purchase_acc_year    := TMP_CUR.PURCHASE_ACC_YEAR;
        v_num_redeemfare           := TMP_CUR.REDEEMFARE;
        v_num_fst_day_of_month     := TMP_CUR.FST_DAY_OF_MONTH;
        v_num_fst_day_of_quarter   := TMP_CUR.FST_DAY_OF_QUARTER;
        v_num_fst_day_of_year      := TMP_CUR.FST_DAY_OF_YEAR;
        v_str_agencyno             := TMP_CUR.AGENCYNO;
      END IF;

      v_num_commit_cnt := v_num_commit_cnt + 1;
      IF v_num_commit_cnt = v_num_commit_rows THEN
        COMMIT;
        v_num_commit_cnt := 0;
      END IF;

    END LOOP;
    COMMIT;

    INSERT INTO TMP_fact_emp_income_d_6
      (sk_confirmdate,
       sk_dept,
       sk_emp,
       bk_fundcode,
       sk_agency,
       redeem_acc_month,
       redeem_acc_quarter,
       redeem_acc_year,
       shares_init_month,
       shares_init_quarter,
       shares_init_year,
       purchase_acc_month,
       purchase_acc_quarter,
       purchase_acc_year,
       redeemfare,
       PURCHASE_SHARES,
       REDEEM_SHARES,
       AGENCYNO)
      select t5.sk_confirmdate,
             t5.sk_dept,
             t5.sk_emp,
             t5.bk_fundcode,
             t5.sk_agency,
             0                 as redeem_acc_month,
             0                 as redeem_acc_quarter,
             0                 as redeem_acc_year,
             t5.shares_init,
             t5.shares_init,
             t5.shares_init,
             0                 as purchase_acc_month,
             0                 as purchase_acc_quarter,
             0                 as purchase_acc_year,
             0                 as redeemfare,
             0                 as purchase_shares,
             0                 as redeem_shares,
             T5.AGENCYNO
        from tmp_fact_emp_income_d_5 t5
        left join tmp_fact_emp_income_d_3 t3
          on (t5.sk_confirmdate = t3.sk_confirmdate and
             t5.bk_fundcode = t3.bk_fundcode and
             t5.sk_agency = t3.sk_agency and t5.sk_emp = t3.sk_emp and
             t5.sk_dept = t3.sk_dept)
       where t3.sk_emp is null;
    commit;

    DELETE FROM FACT_EMP_INCOME_D
     WHERE SK_CONFIRMDATE BETWEEN :startdate AND :enddate;
    COMMIT;

    DELETE FROM TMP_FACT_EMP_INCOME_D_6
     WHERE SK_CONFIRMDATE < :startdate;
    COMMIT;

    INSERT INTO fact_emp_income_d
      (sk_confirmdate,
       sk_dept,
       sk_emp,
       bk_fundcode,
       sk_agency,
       redeem_acc_month,
       redeem_acc_quarter,
       redeem_acc_year,
       shares_init_month,
       shares_init_quarter,
       shares_init_year,
       purchase_acc_month,
       purchase_acc_quarter,
       purchase_acc_year,
       redeemfare,
       PURCHASE_SHARES,
       REDEEM_SHARES,
       AGENCYNO)
      SELECT sk_confirmdate,
             sk_dept,
             sk_emp,
             bk_fundcode,
             sk_agency,
             redeem_acc_month,
             redeem_acc_quarter,
             redeem_acc_year,
             shares_init_month,
             shares_init_quarter,
             shares_init_year,
             purchase_acc_month,
             purchase_acc_quarter,
             purchase_acc_year,
             redeemfare,
             purchase_shares,
             redeem_shares,
             AGENCYNO
        FROM TMP_FACT_EMP_INCOME_D_6;
    COMMIT;

    --加载后处理
    --处理EFFECTIVE_TO字段
    truncate table TMP_FACT_EMP_INCOME_D_7;
    update fact_emp_income_d t
       set t.effective_to =
           (select nvl(to_number(to_char(to_date(min(d.sk_confirmdate),
                                                 'yyyymmdd') - 1,
                                         'yyyymmdd')),
                       20991231)
              from fact_emp_income_d d
             where d.sk_dept = t.sk_dept
               and d.sk_emp = t.sk_emp
               and d.bk_fundcode = t.bk_fundcode
               and d.sk_agency = t.sk_agency
               and d.agencyno = t.agencyno
               and d.sk_confirmdate > t.sk_confirmdate)
     where t.effective_to is null
        OR T.EFFECTIVE_TO = 20991231;
    commit;
    --当EFFECTIVE_FROM、EFFECTIVE_TO跨月时需要将数据拆分
    FOR TMP_CUR IN (select sk_confirmdate,
                           sk_dept,
                           sk_emp,
                           bk_fundcode,
                           sk_agency,
                           redeem_acc_month,
                           redeem_acc_quarter,
                           redeem_acc_year,
                           shares_init_month,
                           shares_init_quarter,
                           shares_init_year,
                           purchase_acc_month,
                           purchase_acc_quarter,
                           purchase_acc_year,
                           redeemfare,
                           purchase_shares,
                           redeem_shares,
                           effective_to,
                           agencyno
                      from fact_emp_income_d T
                     WHERE FLOOR(T.SK_CONFIRMDATE / 100) <>
                           FLOOR(T.EFFECTIVE_TO / 100)
                       AND T.EFFECTIVE_TO <> 20991231
                     ORDER BY T.SK_DEPT,
                              T.SK_EMP,
                              T.BK_FUNDCODE,
                              T.SK_AGENCY,
                              T.SK_CONFIRMDATE) LOOP

      v_num_effective_to := to_number(to_char(last_day(to_date(tmp_cur.sk_confirmdate,
                                                               'yyyymmdd')),
                                              'yyyymmdd'));

      insert into tmp_fact_emp_income_d_7
        (sk_confirmdate,
         sk_dept,
         sk_emp,
         bk_fundcode,
         sk_agency,
         redeem_acc_month,
         redeem_acc_quarter,
         redeem_acc_year,
         shares_init_month,
         shares_init_quarter,
         shares_init_year,
         purchase_acc_month,
         purchase_acc_quarter,
         purchase_acc_year,
         redeemfare,
         purchase_shares,
         redeem_shares,
         effective_to,
         agencyno)
      values
        (tmp_cur.sk_confirmdate,
         tmp_cur.sk_dept,
         tmp_cur.sk_emp,
         tmp_cur.bk_fundcode,
         tmp_cur.sk_agency,
         tmp_cur.redeem_acc_month,
         tmp_cur.redeem_acc_quarter,
         tmp_cur.redeem_acc_year,
         tmp_cur.shares_init_month,
         tmp_cur.shares_init_quarter,
         tmp_cur.shares_init_year,
         tmp_cur.purchase_acc_month,
         tmp_cur.purchase_acc_quarter,
         tmp_cur.purchase_acc_year,
         tmp_cur.redeemfare,
         tmp_cur.purchase_shares,
         tmp_cur.redeem_shares,
         v_num_effective_to,
         tmp_cur.agencyno);

      select dmtm.yq_cur, dmtm.y_cur
        into v_num_quarter_pre, v_num_year_pre
        from dim_time dmtm
       where dmtm.sk_date = tmp_cur.sk_confirmdate;

      LOOP
        v_num_sk_confirmdate := to_number(to_char(to_date(v_num_effective_to,
                                                          'yyyymmdd') + 1,
                                                  'yyyymmdd'));
        IF FLOOR(v_num_sk_confirmdate / 100) =
           FLOOR(TMP_CUR.EFFECTIVE_TO / 100) THEN

          v_num_effective_to := TMP_CUR.EFFECTIVE_TO;
          select dmtm.yq_cur, dmtm.y_cur
            into v_num_quarter_cur, v_num_year_cur
            from dim_time dmtm
           where dmtm.sk_date = v_num_sk_confirmdate;

          IF v_num_quarter_cur = v_num_quarter_pre THEN
            insert into tmp_fact_emp_income_d_7
              (sk_confirmdate,
               sk_dept,
               sk_emp,
               bk_fundcode,
               sk_agency,
               redeem_acc_month,
               redeem_acc_quarter,
               redeem_acc_year,
               shares_init_month,
               shares_init_quarter,
               shares_init_year,
               purchase_acc_month,
               purchase_acc_quarter,
               purchase_acc_year,
               redeemfare,
               purchase_shares,
               redeem_shares,
               effective_to,
               agencyno)
            values
              (v_num_sk_confirmdate,
               tmp_cur.sk_dept,
               tmp_cur.sk_emp,
               tmp_cur.bk_fundcode,
               tmp_cur.sk_agency,
               0,
               tmp_cur.redeem_acc_quarter,
               tmp_cur.redeem_acc_year,
               tmp_cur.shares_init_month + tmp_cur.purchase_acc_month -
               tmp_cur.redeem_acc_month,
               tmp_cur.shares_init_quarter,
               tmp_cur.shares_init_year,
               0,
               tmp_cur.purchase_acc_quarter,
               tmp_cur.purchase_acc_year,
               tmp_cur.redeemfare,
               tmp_cur.purchase_shares,
               tmp_cur.redeem_shares,
               v_num_effective_to,
               tmp_cur.agencyno);
          ELSE
            IF v_num_year_cur = v_num_year_pre THEN
              insert into tmp_fact_emp_income_d_7
                (sk_confirmdate,
                 sk_dept,
                 sk_emp,
                 bk_fundcode,
                 sk_agency,
                 redeem_acc_month,
                 redeem_acc_quarter,
                 redeem_acc_year,
                 shares_init_month,
                 shares_init_quarter,
                 shares_init_year,
                 purchase_acc_month,
                 purchase_acc_quarter,
                 purchase_acc_year,
                 redeemfare,
                 purchase_shares,
                 redeem_shares,
                 effective_to,
                 agencyno)
              values
                (v_num_sk_confirmdate,
                 tmp_cur.sk_dept,
                 tmp_cur.sk_emp,
                 tmp_cur.bk_fundcode,
                 tmp_cur.sk_agency,
                 0,
                 0,
                 tmp_cur.redeem_acc_year,
                 tmp_cur.shares_init_month + tmp_cur.purchase_acc_month -
                 tmp_cur.redeem_acc_month,
                 tmp_cur.shares_init_quarter + tmp_cur.purchase_acc_quarter -
                 tmp_cur.redeem_acc_quarter,
                 tmp_cur.shares_init_year,
                 0,
                 0,
                 tmp_cur.purchase_acc_year,
                 tmp_cur.redeemfare,
                 tmp_cur.purchase_shares,
                 tmp_cur.redeem_shares,
                 v_num_effective_to,
                 tmp_cur.agencyno);
            ELSE
              insert into tmp_fact_emp_income_d_7
                (sk_confirmdate,
                 sk_dept,
                 sk_emp,
                 bk_fundcode,
                 sk_agency,
                 redeem_acc_month,
                 redeem_acc_quarter,
                 redeem_acc_year,
                 shares_init_month,
                 shares_init_quarter,
                 shares_init_year,
                 purchase_acc_month,
                 purchase_acc_quarter,
                 purchase_acc_year,
                 redeemfare,
                 purchase_shares,
                 redeem_shares,
                 effective_to,
                 agencyno)
              values
                (v_num_sk_confirmdate,
                 tmp_cur.sk_dept,
                 tmp_cur.sk_emp,
                 tmp_cur.bk_fundcode,
                 tmp_cur.sk_agency,
                 0,
                 0,
                 0,
                 tmp_cur.shares_init_month + tmp_cur.purchase_acc_month -
                 tmp_cur.redeem_acc_month,
                 tmp_cur.shares_init_quarter + tmp_cur.purchase_acc_quarter -
                 tmp_cur.redeem_acc_quarter,
                 tmp_cur.shares_init_year + tmp_cur.purchase_acc_year -
                 tmp_cur.redeem_acc_year,
                 0,
                 0,
                 0,
                 tmp_cur.redeemfare,
                 tmp_cur.purchase_shares,
                 tmp_cur.redeem_shares,
                 v_num_effective_to,
                 tmp_cur.agencyno);
            END IF;
          end if;

        ELSE

          v_num_effective_to := to_number(to_char(last_day(to_date(v_num_sk_confirmdate,
                                                                   'yyyymmdd')),
                                                  'yyyymmdd'));
          select dmtm.yq_cur, dmtm.y_cur
            into v_num_quarter_cur, v_num_year_cur
            from dim_time dmtm
           where dmtm.sk_date = v_num_sk_confirmdate;

          IF v_num_quarter_cur = v_num_quarter_pre THEN
            insert into tmp_fact_emp_income_d_7
              (sk_confirmdate,
               sk_dept,
               sk_emp,
               bk_fundcode,
               sk_agency,
               redeem_acc_month,
               redeem_acc_quarter,
               redeem_acc_year,
               shares_init_month,
               shares_init_quarter,
               shares_init_year,
               purchase_acc_month,
               purchase_acc_quarter,
               purchase_acc_year,
               redeemfare,
               purchase_shares,
               redeem_shares,
               effective_to,
               agencyno)
            values
              (v_num_sk_confirmdate,
               tmp_cur.sk_dept,
               tmp_cur.sk_emp,
               tmp_cur.bk_fundcode,
               tmp_cur.sk_agency,
               0,
               tmp_cur.redeem_acc_quarter,
               tmp_cur.redeem_acc_year,
               tmp_cur.shares_init_month + tmp_cur.purchase_acc_month -
               tmp_cur.redeem_acc_month,
               tmp_cur.shares_init_quarter,
               tmp_cur.shares_init_year,
               0,
               tmp_cur.purchase_acc_quarter,
               tmp_cur.purchase_acc_year,
               tmp_cur.redeemfare,
               tmp_cur.purchase_shares,
               tmp_cur.redeem_shares,
               v_num_effective_to,
               tmp_cur.agencyno);
          ELSE
            IF v_num_year_cur = v_num_year_pre THEN
              insert into tmp_fact_emp_income_d_7
                (sk_confirmdate,
                 sk_dept,
                 sk_emp,
                 bk_fundcode,
                 sk_agency,
                 redeem_acc_month,
                 redeem_acc_quarter,
                 redeem_acc_year,
                 shares_init_month,
                 shares_init_quarter,
                 shares_init_year,
                 purchase_acc_month,
                 purchase_acc_quarter,
                 purchase_acc_year,
                 redeemfare,
                 purchase_shares,
                 redeem_shares,
                 effective_to,
                 agencyno)
              values
                (v_num_sk_confirmdate,
                 tmp_cur.sk_dept,
                 tmp_cur.sk_emp,
                 tmp_cur.bk_fundcode,
                 tmp_cur.sk_agency,
                 0,
                 0,
                 tmp_cur.redeem_acc_year,
                 tmp_cur.shares_init_month + tmp_cur.purchase_acc_month -
                 tmp_cur.redeem_acc_month,
                 tmp_cur.shares_init_quarter + tmp_cur.purchase_acc_quarter -
                 tmp_cur.redeem_acc_quarter,
                 tmp_cur.shares_init_year,
                 0,
                 0,
                 tmp_cur.purchase_acc_year,
                 tmp_cur.redeemfare,
                 tmp_cur.purchase_shares,
                 tmp_cur.redeem_shares,
                 v_num_effective_to,
                 tmp_cur.agencyno);
            ELSE
              insert into tmp_fact_emp_income_d_7
                (sk_confirmdate,
                 sk_dept,
                 sk_emp,
                 bk_fundcode,
                 sk_agency,
                 redeem_acc_month,
                 redeem_acc_quarter,
                 redeem_acc_year,
                 shares_init_month,
                 shares_init_quarter,
                 shares_init_year,
                 purchase_acc_month,
                 purchase_acc_quarter,
                 purchase_acc_year,
                 redeemfare,
                 purchase_shares,
                 redeem_shares,
                 effective_to,
                 agencyno)
              values
                (v_num_sk_confirmdate,
                 tmp_cur.sk_dept,
                 tmp_cur.sk_emp,
                 tmp_cur.bk_fundcode,
                 tmp_cur.sk_agency,
                 0,
                 0,
                 0,
                 tmp_cur.shares_init_month + tmp_cur.purchase_acc_month -
                 tmp_cur.redeem_acc_month,
                 tmp_cur.shares_init_quarter + tmp_cur.purchase_acc_quarter -
                 tmp_cur.redeem_acc_quarter,
                 tmp_cur.shares_init_year + tmp_cur.purchase_acc_year -
                 tmp_cur.redeem_acc_year,
                 0,
                 0,
                 0,
                 tmp_cur.redeemfare,
                 tmp_cur.purchase_shares,
                 tmp_cur.redeem_shares,
                 v_num_effective_to,
                 tmp_cur.agencyno);
            END IF;
          END IF;

          v_num_quarter_pre := v_num_quarter_cur;
          v_num_year_pre    := v_num_year_cur;
        END IF;

        EXIT WHEN FLOOR(v_num_sk_confirmdate / 100) = FLOOR(TMP_CUR.EFFECTIVE_TO / 100);
      END LOOP;

    END LOOP;

    DELETE FROM TMP_FACT_EMP_INCOME_D_7 T
     WHERE MOD(T.EFFECTIVE_TO, 100) = 1
       AND T.SK_CONFIRMDATE = T.EFFECTIVE_TO;

    commit;

    MERGE INTO FACT_EMP_INCOME_D FT
    USING TMP_FACT_EMP_INCOME_D_7 T
    ON (FT.SK_DEPT = T.SK_DEPT AND FT.SK_EMP = T.SK_EMP AND FT.BK_FUNDCODE = T.BK_FUNDCODE AND FT.SK_AGENCY = T.SK_AGENCY AND FT.SK_CONFIRMDATE = T.SK_CONFIRMDATE AND FT.AGENCYNO = T.AGENCYNO)
    WHEN MATCHED THEN
      UPDATE SET FT.EFFECTIVE_TO = T.EFFECTIVE_TO
    WHEN NOT MATCHED THEN
      INSERT
        (sk_confirmdate,
         sk_dept,
         sk_emp,
         bk_fundcode,
         sk_agency,
         redeem_acc_month,
         redeem_acc_quarter,
         redeem_acc_year,
         shares_init_month,
         shares_init_quarter,
         shares_init_year,
         purchase_acc_month,
         purchase_acc_quarter,
         purchase_acc_year,
         redeemfare,
         purchase_shares,
         redeem_shares,
         effective_to,
         agencyno)
      VALUES
        (T.sk_confirmdate,
         T.sk_dept,
         T.sk_emp,
         T. bk_fundcode,
         T. sk_agency,
         T.redeem_acc_month,
         T.redeem_acc_quarter,
         T. redeem_acc_year,
         T.shares_init_month,
         T.shares_init_quarter,
         T. shares_init_year,
         T. purchase_acc_month,
         T. purchase_acc_quarter,
         T. purchase_acc_year,
         T.redeemfare,
         T.purchase_shares,
         T. redeem_shares,
         T. effective_to,
         T.AGENCYNO);
    COMMIT;